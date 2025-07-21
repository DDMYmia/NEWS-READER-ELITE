"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "sonner"

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

  const API_BASE = "http://localhost:8000/api"

  useEffect(() => {
    loadData()
  }, [])

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
        <div className="flex space-x-2">
          <Button 
            onClick={() => collectNews('api')} 
            disabled={collecting}
            variant="outline"
          >
            {collecting ? "Collecting..." : "Collect API News"}
          </Button>
          <Button 
            onClick={() => collectNews('rss')} 
            disabled={collecting}
            variant="outline"
          >
            {collecting ? "Collecting..." : "Collect RSS News"}
          </Button>
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
    </div>
  )
}
