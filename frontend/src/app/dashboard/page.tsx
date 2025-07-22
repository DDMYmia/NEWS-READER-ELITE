"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"

interface NewsArticle {
  id: number
  title: string
  description: string
  url: string
  source_name: string
  published_at: string
  language: string
  tags?: string[]
  tickers?: string[]
}

interface Stats {
  database_count: number
  source_stats: Record<string, number>
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

  const API_BASE = "http://localhost:8000/api"
  const WS_URL = "ws://localhost:8000/ws/logs"

  useEffect(() => {
    loadData()
    connectLogWS()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 新增：定时刷新自动采集状态
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
    const timer = setInterval(checkStatus, 5000)
    return () => clearInterval(timer)
  }, [])

  // 定时刷新自动采集状态和新增条数
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
    const timer = setInterval(checkStatus, 3000)
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
  const connectLogWS = () => {
    if (wsRef.current) {
      wsRef.current.onclose = null; // 防止多次触发
      wsRef.current.onerror = null;
      wsRef.current.close();
    }
    const ws = new window.WebSocket(WS_URL)
    ws.onmessage = (event) => {
      setConsoleLines((lines) => [...lines, event.data])
    }
    ws.onopen = () => {
      setConsoleLines((lines) => [...lines, "[Console] Connected to backend log stream."])
    }
    ws.onclose = () => {
      setConsoleLines((lines) => [...lines, "[Console] Disconnected from backend log stream."])
      wsRef.current = null;
      // 自动重连，防止多次重连
      setTimeout(() => {
        if (!wsRef.current) connectLogWS()
      }, 2000)
    }
    ws.onerror = () => {
      setConsoleLines((lines) => [...lines, "[Console] Log WebSocket error."])
    }
    wsRef.current = ws
  }

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
        await loadData() // Reload data
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
    if (!autoApi) {
      setConsoleLines((lines) => [...lines, "> [API] auto start"])
      await fetch("http://localhost:8000/api/auto/start_api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval: 180 })
      })
    } else {
      setConsoleLines((lines) => [...lines, "> [API] auto stop"])
      await fetch("http://localhost:8000/api/auto/stop_api", { method: "POST" })
    }
  }
  // 自动RSS采集按钮
  const handleAutoRssBtn = async () => {
    if (!autoRss) {
      setConsoleLines((lines) => [...lines, "> [RSS] auto start"])
      await fetch("http://localhost:8000/api/auto/start_rss", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval: 180 })
      })
    } else {
      setConsoleLines((lines) => [...lines, "> [RSS] auto stop"])
      await fetch("http://localhost:8000/api/auto/stop_rss", { method: "POST" })
    }
  }
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
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.database_count || 0}</div>
                <p className="text-xs text-muted-foreground">
                  Last updated: {stats?.last_updated ? formatDate(stats.last_updated) : 'N/A'}
                </p>
              </CardContent>
            </Card>

            {stats?.source_stats && Object.entries(stats.source_stats).map(([source, count]) => (
              <Card key={source}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{source}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{count}</div>
                  <p className="text-xs text-muted-foreground">articles</p>
                </CardContent>
              </Card>
            ))}
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
                    <TableHead>Title</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Published</TableHead>
                    <TableHead>Language</TableHead>
                    <TableHead>Actions</TableHead>
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

      {/* 控制台区域 */}
      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Console</CardTitle>
            <CardDescription>Real-time logs and command input</CardDescription>
          </CardHeader>
          <CardContent>
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
