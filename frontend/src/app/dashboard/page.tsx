"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"

interface NewsArticle {
  id: string
  title: string
  description: string
  url: string
  image_url?: string
  published_at: string
  source_name: string
  source_url?: string
  language: string
  topics?: string[]
  tickers?: string[]
  authors?: string[]
  full_content?: string
}

interface Stats {
  database_count: number
  mongodb_backup_count: number // Add MongoDB count
  rss_file_count: number // Add specific file counts
  newsapi_ai_file_count: number
  thenewsapi_file_count: number
  newsdata_file_count: number
  tiingo_file_count: number
  alpha_vantage_file_count: number
  last_updated: string
}

interface RssSource {
  name: string
  url: string
}

interface Sources {
  api: string[]
  rss: RssSource[]
}

export default function DashboardPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [sources, setSources] = useState<Sources | null>(null)
  const [loading, setLoading] = useState(true)
  const [collecting, setCollecting] = useState(false)
  const [autoCollecting, setAutoCollecting] = useState(false)
  const [consoleLines, setConsoleLines] = useState<string[]>([])
  const [command, setCommand] = useState("")
  const consoleRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const [autoApi, setAutoApi] = useState(false)
  const [autoRss, setAutoRss] = useState(false)
  const [apiNew, setApiNew] = useState(0)
  const [rssNew, setRssNew] = useState(0)
  // const [alphaVantageNew, setAlphaVantageNew] = useState(0) // 移除 AlphaVantage 新增计数
  // const [autoAlphaVantage, setAutoAlphaVantage] = useState(false) // 移除 AlphaVantage 自动采集状态

  // 新增：实时新闻流状态
  const [realtimeNewsFeed, setRealtimeNewsFeed] = useState<NewsArticle[]>([])

  const API_BASE = "http://localhost:8000/api"
  const WS_URL = "ws://localhost:8000/ws/logs"

  useEffect(() => {
    loadData()
    connectLogWS()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 新增：定时刷新自动采集状态 (可以调整为更长时间的备用轮询)
  useEffect(() => {
    let lastStatus: boolean | null = null
    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/command`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cmd: "status" })
        })
        const data = await res.json()
        const running = String(data.result).includes("True")
        setAutoCollecting(running)
        // 只在状态变化时输出到控制台
        if (lastStatus === null) {
          lastStatus = running
        } else if (lastStatus !== running) {
          setConsoleLines((lines) => [...lines, `[Status] Auto collection running: ${running}`])
          lastStatus = running
        }
      } catch {}
    }
    checkStatus()
    // 将此轮询间隔调长，作为 WebSocket 的备用/心跳
    const timer = setInterval(checkStatus, 30000) // 例如 30 秒
    return () => clearInterval(timer)
  }, [])

  // 定时刷新自动采集状态和新增条数 (此轮询频率可以调低或移除，主要依赖 WebSocket 推送)
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/auto/status")
        const data = await res.json()
        setAutoApi(!!data.api_running)
        setAutoRss(!!data.rss_running)
        setApiNew(data.api_new || 0)
        setRssNew(data.rss_new || 0)
      } catch {}
    }
    checkStatus()
    // 将此轮询间隔调长，作为 WebSocket 的备用/心跳
    const timer = setInterval(checkStatus, 30000) // 例如 30 秒
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    // 控制台自动滚动到底部
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight
    }
  }, [consoleLines])

  const loadData = async () => {
    setLoading(true)
    try {
      const [newsRes, statsRes, sourcesRes] = await Promise.all([
        fetch(`${API_BASE}/news?limit=100`),
        fetch(`${API_BASE}/stats`),
        fetch(`${API_BASE}/sources`)
      ])

      if (newsRes.ok) {
        const newsData = await newsRes.json()
        setArticles(newsData.articles || [])
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setStats(statsData)
      }

      if (sourcesRes.ok) {
        const sourcesData = await sourcesRes.json()
        setSources(sourcesData.sources)
      }
    } catch (error) {
      toast.error("Failed to load data")
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  // WebSocket 日志流自动重连优化
  const connectLogWS = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.onclose = null; // 防止多次触发
      wsRef.current.onerror = null;
      wsRef.current.close();
    }
    
    const startTime = Date.now(); // Record start time
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws;
    let retries = 0;

    ws.onopen = () => {
      const latency = Date.now() - startTime; // Calculate latency
      setConsoleLines((prev) => [
        ...prev,
        `[Console] Connected to backend log stream. Latency: ${latency}ms.`,
      ]);
      // setAutoCollecting(true) // 此行与日志流连接无关，已移除
      retries = 0; // Reset retries on successful connection
    };

    ws.onmessage = (event) => {
      try {
        console.log("Raw WebSocket message received:", event.data); // Debug: Log raw message
        const message = JSON.parse(event.data);
        console.log("Parsed WebSocket message:", message); // Debug: Log parsed message

        if (message.type === "data_update") {
          if (message.payload.type === "news_update") {
            console.log("News update payload received:", message.payload.new_articles_list); // Debug: Log new articles list
            // 处理新闻文章更新消息
            setApiNew(message.payload.api_new || 0);
            setRssNew(message.payload.rss_new || 0);
            setStats(prevStats => ({ 
              ...prevStats, 
              database_count: message.payload.total_articles || 0, 
              mongodb_backup_count: message.payload.total_articles_mongo || 0, // Ensure MongoDB count is updated
              last_updated: new Date().toISOString() 
            }));
            // 将新文章添加到现有文章列表的顶部
            setArticles(prevArticles => [...(message.payload.new_articles_list || []).map(article => ({
              ...article,
              published_at: new Date(article.published_at).toLocaleString() // 确保日期格式化
            })), ...prevArticles]);
            // 同时更新实时新闻流，限制数量
            setRealtimeNewsFeed(prevFeed => [
              ...(message.payload.new_articles_list || []).map(article => ({
                ...article,
                published_at: new Date(article.published_at).toLocaleString() // 确保日期格式化
              })),
              ...prevFeed
            ].slice(0, 10)); // 只保留最新的 10 篇

            setConsoleLines((lines) => [...lines, `[Data Update] New API: ${message.payload.api_new}, New RSS: ${message.payload.rss_new}, Total: ${message.payload.total_articles}`]);
          } else {
            // 处理其他类型的数据更新消息（目前只有计数更新）
            setApiNew(message.payload.api_new || 0);
            setRssNew(message.payload.rss_new || 0);
            loadData(); // 触发数据重新加载以更新文章列表和总数
            setConsoleLines((lines) => [...lines, `[Data Update] New API: ${message.payload.api_new}, New RSS: ${message.payload.rss_new}, Total: ${message.payload.total_articles}`]);
          }
        } else if (message.type === "log") {
          // 处理普通日志消息
          setConsoleLines((lines) => [...lines, message.message]);
        } else {
          // 无法识别的JSON消息，当作普通日志处理
          setConsoleLines((lines) => [...lines, event.data]);
        }
      } catch (e) {
        // 不是JSON格式的消息，当作普通日志处理
        setConsoleLines((lines) => [...lines, event.data]);
      }
      retries = 0; // 成功接收消息后重置尝试次数
    }
    ws.onclose = () => {
      setConsoleLines((lines) => [...lines, "[Console] Disconnected from backend log stream."])
      wsRef.current = null;
      // 自动重连，指数退避
      const nextAttempt = retries + 1;
      const reconnectTimeout = Math.min(1000 * Math.pow(2, nextAttempt), 30 * 1000); // 最长 30 秒
      setTimeout(() => {
        if (!wsRef.current) connectLogWS()
      }, reconnectTimeout)
    }
    ws.onerror = () => {
      setConsoleLines((lines) => [...lines, "[Console] Log WebSocket error."])
      wsRef.current = null;
      // 错误时也尝试重连，使用指数退避
      const nextAttempt = retries + 1;
      const reconnectTimeout = Math.min(1000 * Math.pow(2, nextAttempt), 30 * 1000); // 最长 30 秒
      setTimeout(() => {
        if (!wsRef.current) connectLogWS()
      }, reconnectTimeout)
    }
  }, [])

  // 持续获取（自动采集）
  const toggleAutoCollect = async () => {
    if (!autoCollecting) {
      // 启动自动采集
      const res = await fetch(`${API_BASE}/auto/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval: 180 })
      })
      const data = await res.json()
      if (data.success) {
        setAutoCollecting(true)
        toast.success("Auto collection started")
      } else {
        toast.error(data.message || "Failed to start auto collection")
      }
    } else {
      // 停止自动采集
      const res = await fetch(`${API_BASE}/auto/stop`, { method: "POST" })
      const data = await res.json()
      if (data.success) {
        setAutoCollecting(false)
        toast.success("Auto collection stopped")
      } else {
        toast.error(data.message || "Failed to stop auto collection")
      }
    }
  }

  // 单次采集
  const collectNews = async (type: 'api' | 'rss') => {
    setCollecting(true)
    try {
      const response = await fetch(`${API_BASE}/collect/${type}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        toast.success(`${type.toUpperCase()} collection completed`)
        // await loadData() // 移除这里的 loadData()，改用 WebSocket 推送触发
      } else {
        toast.error(`Failed to collect ${type} news`)
      }
    } catch (error) {
      toast.error(`Error collecting ${type} news`)
      console.error(error)
    } finally {
      setCollecting(false)
    }
  }

  // 命令输入处理
  const handleCommandSend = async () => {
    if (!command.trim()) return
    setConsoleLines((lines) => [...lines, `> ${command}`])
    try {
      const res = await fetch(`${API_BASE}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cmd: command })
      })
      const data = await res.json()
      setConsoleLines((lines) => [...lines, `[Result] ${data.result}`])
    } catch (e) {
      setConsoleLines((lines) => [...lines, `[Error] Command failed`])
    }
    setCommand("")
  }

  // 联动命令执行
  const runConsoleCommand = async (cmd: string) => {
    setConsoleLines((lines) => [...lines, `> ${cmd}`])
    try {
      const res = await fetch(`${API_BASE}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cmd })
      })
      const data = await res.json()
      setConsoleLines((lines) => [...lines, `[Result] ${data.result}`])
      // 状态命令特殊处理
      if (cmd === "auto start") setAutoCollecting(true)
      if (cmd === "auto stop") setAutoCollecting(false)
    } catch (e) {
      setConsoleLines((lines) => [...lines, `[Error] Command failed`])
    }
  }

  // 自动API采集按钮
  const handleAutoApiBtn = async () => {
    const isStarting = !autoApi;
    setConsoleLines((lines) => [
      ...lines,
      isStarting ? "> [API] auto start" : "> [API] auto stop",
    ]);
    setAutoApi(isStarting); // 立即乐观更新状态
    try {
      const res = await fetch(
        isStarting
          ? "http://localhost:8000/api/auto/start_api"
          : "http://localhost:8000/api/auto/stop_api",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ interval: 180 }),
        }
      );
      const data = await res.json();
      if (data.success) {
        toast.success(isStarting ? "Auto API collection started" : "Auto API collection stopped");
      } else {
        toast.error(data.message || "Failed to change auto API collection state");
        setAutoApi(!isStarting); // 如果失败，回滚状态
      }
    } catch (error) {
      toast.error("Network error or backend issue");
      console.error(error);
      setAutoApi(!isStarting); // 网络错误，回滚状态
    }
  };
  // 自动RSS采集按钮
  const handleAutoRssBtn = async () => {
    const isStarting = !autoRss;
    setConsoleLines((lines) => [
      ...lines,
      isStarting ? "> [RSS] auto start" : "> [RSS] auto stop",
    ]);
    setAutoRss(isStarting); // 立即乐观更新状态
    try {
      const res = await fetch(
        isStarting
          ? "http://localhost:8000/api/auto/start_rss"
          : "http://localhost:8000/api/auto/stop_rss",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ interval: 180 }),
        }
      );
      const data = await res.json();
      if (data.success) {
        toast.success(isStarting ? "Auto RSS collection started" : "Auto RSS collection stopped");
      } else {
        toast.error(data.message || "Failed to change auto RSS collection state");
        setAutoRss(!isStarting); // 如果失败，回滚状态
      }
    } catch (error) {
      toast.error("Network error or backend issue");
      console.error(error);
      setAutoRss(!isStarting); // 网络错误，回滚状态
    }
  };
  // 新增条目数点击后归零
  const resetApiNew = async () => {
    await fetch("http://localhost:8000/api/auto/reset_new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "api" })
    })
    setApiNew(0)
  }
  const resetRssNew = async () => {
    await fetch("http://localhost:8000/api/auto/reset_new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "rss" })
    })
    setRssNew(0)
  }

  const handleCommandKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleCommandSend()
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const truncateText = (text: string, maxLength: number = 100) => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
  }

  if (loading) {
    return (
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">News Reader Elite</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-[100px]" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-[60px]" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">News Reader Elite</h2>
        <div className="flex space-x-4 items-center">
          {/* 自动API采集按钮 */}
          <div className="flex items-center space-x-1">
            <Button
              onClick={handleAutoApiBtn}
              variant={autoApi ? "default" : "outline"}
            >
              {autoApi ? "Stop Auto API" : "Start Auto API"}
            </Button>
            <span className="flex items-center ml-1">
              {autoApi ? (
                <Loader2 className="animate-spin w-5 h-5 text-green-500" />
              ) : (
                <Loader2 className="w-5 h-5 text-gray-400" />
              )}
              <span className={`ml-1 text-xs ${autoApi ? 'text-green-500' : 'text-gray-400'}`}>{autoApi ? 'Running' : 'Stopped'}</span>
              {apiNew > 0 && (
                <span onClick={resetApiNew} className="ml-2 px-2 py-0.5 rounded bg-green-100 text-green-700 text-xs cursor-pointer hover:bg-green-200">+{apiNew}</span>
              )}
            </span>
          </div>
          {/* 自动RSS采集按钮 */}
          <div className="flex items-center space-x-1">
            <Button
              onClick={handleAutoRssBtn}
              variant={autoRss ? "default" : "outline"}
            >
              {autoRss ? "Stop Auto RSS" : "Start Auto RSS"}
            </Button>
            <span className="flex items-center ml-1">
              {autoRss ? (
                <Loader2 className="animate-spin w-5 h-5 text-blue-500" />
              ) : (
                <Loader2 className="w-5 h-5 text-gray-400" />
              )}
              <span className={`ml-1 text-xs ${autoRss ? 'text-blue-500' : 'text-gray-400'}`}>{autoRss ? 'Running' : 'Stopped'}</span>
              {rssNew > 0 && (
                <span onClick={resetRssNew} className="ml-2 px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-xs cursor-pointer hover:bg-blue-200">+{rssNew}</span>
              )}
            </span>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="news">News Articles</TabsTrigger>
          <TabsTrigger value="sources">Sources</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            {/* Combined Total Articles Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1">
                <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
              </CardHeader>
              <CardContent className="pt-1">
                <div className="space-y-0.5">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted-foreground">PostgreSQL:</span>
                    <span className="text-lg font-bold">{stats?.database_count || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted-foreground">MongoDB:</span>
                    <span className="text-lg font-bold">{stats?.mongodb_backup_count || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted-foreground">Local JSON:</span>
                    <span className="text-lg font-bold">
                      {stats ? (
                        (stats.rss_file_count || 0) + 
                        (stats.newsapi_ai_file_count || 0) + 
                        (stats.thenewsapi_file_count || 0) + 
                        (stats.newsdata_file_count || 0) + 
                        (stats.tiingo_file_count || 0) + 
                        (stats.alpha_vantage_file_count || 0)
                      ) : 0}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Last updated: {stats?.last_updated ? formatDate(stats.last_updated) : 'N/A'}
                </p>
              </CardContent>
            </Card>

            {/* Dynamically render individual file counts for detailed view */}
            {stats && Object.entries(stats).map(([key, value]) => {
              if (key.endsWith('_file_count')) {
                const displayName = key.replace('_file_count', '').replace(/_/g, ' ').replace(/(\b\w)/g, s => s.toUpperCase());
                return (
                  <Card key={key}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1">
                      <CardTitle className="text-sm font-medium">{displayName} File</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-1">
                      <div className="text-2xl font-bold">{value}</div>
                      <p className="text-xs text-muted-foreground">articles in JSON</p>
                    </CardContent>
                  </Card>
                );
              }
              return null;
            })}
          </div>
        </TabsContent>

        <TabsContent value="news" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Latest News Articles</CardTitle>
              <CardDescription>
                Showing {articles.length} most recent articles
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead><TableHead>Source</TableHead><TableHead>Published</TableHead><TableHead>Language</TableHead><TableHead>Tickers</TableHead>{/* 新增股票代码列 */}<TableHead>Topics</TableHead>{/* 新增主题列 */}<TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {articles.map((article) => (
                    <TableRow key={article.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{truncateText(article.title, 60)}</div>
                          <div className="text-sm text-muted-foreground">
                            {truncateText(article.description, 80)}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{article.source_name}</Badge>
                      </TableCell>
                      <TableCell>{formatDate(article.published_at)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{article.language}</Badge>
                      </TableCell>
                      <TableCell> {/* 显示股票代码 */}
                        {article.tickers && article.tickers.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {article.tickers.map((ticker, idx) => (
                              <Badge key={idx} variant="default">{ticker}</Badge>
                            ))}
                          </div>
                        ) : (
                          "N/A"
                        )}
                      </TableCell>
                      <TableCell> {/* 显示主题 */}
                        {article.topics && article.topics.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {article.topics.map((topic, idx) => (
                              <Badge key={idx} variant="outline">{topic}</Badge>
                            ))}
                          </div>
                        ) : (
                          "N/A"
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(article.url, '_blank')}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sources" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>API Sources</CardTitle>
                <CardDescription>Configured API news sources</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Badge variant="outline" className="mr-2 mb-2">
                    AlphaVantage
                  </Badge>
                  {sources?.api?.map((source, index) => (
                    <Badge key={index} variant="outline" className="mr-2 mb-2">
                      {source}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>RSS Sources</CardTitle>
                <CardDescription>Configured RSS feed sources</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {sources?.rss?.map((source, index) => (
                    <div key={index} className="text-sm">
                      <Badge variant="secondary" className="mr-2">
                        {source.name}
                      </Badge>
                      <span className="text-muted-foreground">{source.url}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* 实时新闻流区域 */}
      <div className="mt-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Real-time News Feed</CardTitle>
            <CardDescription className="text-sm">Latest articles pushed from backend</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="h-64 overflow-y-auto space-y-2 border rounded-md p-2 bg-gray-50">
              {realtimeNewsFeed.length > 0 ? (
                realtimeNewsFeed.map((article, index) => (
                  <div key={`${article.url}-${index}`} className="bg-white rounded p-2 shadow-sm border-l-2 border-blue-500">
                    <h4 className="font-medium text-sm mb-1 leading-tight">{truncateText(article.title, 60)}</h4>
                    {article.description && (
                      <p className="text-xs text-muted-foreground mb-1 leading-tight">{truncateText(article.description, 100)}</p>
                    )}
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{article.source_name}</span>
                        <span>•</span>
                        <span>{formatDate(article.published_at)}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-xs"
                        onClick={() => window.open(article.url, '_blank')}
                      >
                        View
                      </Button>
                    </div>
                    {(article.tickers && article.tickers.length > 0) || (article.topics && article.topics.length > 0) ? (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {article.tickers && article.tickers.map((ticker, idx) => (
                          <Badge key={idx} variant="default" className="text-xs px-1 py-0">{ticker}</Badge>
                        ))}
                        {article.topics && article.topics.map((topic, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs px-1 py-0">{topic}</Badge>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                  No real-time news yet. Start auto collection!
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 控制台区域 */}
      <div className="mt-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Console</CardTitle>
            <CardDescription className="text-sm">Real-time logs and command input</CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <div
              ref={consoleRef}
              className="bg-black text-green-400 font-mono rounded p-2 mb-2 h-64 overflow-y-auto text-xs"
              style={{ minHeight: 200, maxHeight: 300 }}
            >
              {consoleLines.map((line, idx) => (
                <div key={idx}>{line}</div>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                className="flex-1 border rounded px-2 py-1 text-xs bg-zinc-900 text-green-300 outline-none"
                placeholder="Enter command (e.g. collect, status, auto start, help)"
                value={command}
                onChange={e => setCommand(e.target.value)}
                onKeyDown={handleCommandKeyDown}
                autoComplete="off"
              />
              <Button size="sm" variant="secondary" onClick={handleCommandSend}>Send</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
