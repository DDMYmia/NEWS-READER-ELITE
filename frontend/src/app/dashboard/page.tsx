"use client"

import { AppSidebar } from "@/components/app-sidebar"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  Activity, 
  Database,
  Globe,
  Newspaper,
  TrendingUp,
  Users,
  PlayCircle,
  PauseCircle,
  RefreshCw,
  Loader2
} from "lucide-react"
import { useEffect, useState } from "react"

interface NewsStats {
  success: boolean
  database_count: number
  mongodb_backup_count: number
  last_updated: string
  last_api_collection_time: string | null
  last_rss_collection_time: string | null
  total_json_file_count: number
  api_new: number
  rss_new: number
}

interface AutoCollectionStatus {
  api_running: boolean
  rss_running: boolean
  api_new: number // new articles collected in current session
  rss_new: number // new articles collected in current session
  api_total: number // total historical articles from all API sources
  rss_total: number // total historical articles from RSS sources
  api_error_occurred: boolean
  rss_error_occurred: boolean
}

interface NewsArticle {
  id: string
  title: string
  description: string
  source_name: string
  published_at: string
  url: string
}

export default function Page() {
  const [stats, setStats] = useState<NewsStats | null>(null)
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [loading, setLoading] = useState(true)
  const [autoCollectionStatus, setAutoCollectionStatus] = useState<AutoCollectionStatus>({
    api_running: false,
    rss_running: false,
    api_new: 0,
    rss_new: 0,
    api_total: 0,
    rss_total: 0,
    api_error_occurred: false,
    rss_error_occurred: false,
  })

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch statistics
        const statsResponse = await fetch('/api/stats')
        if (statsResponse.ok) {
          const statsData = await statsResponse.json()
          setStats(statsData)
        }

        // Fetch latest articles
        const articlesResponse = await fetch('/api/news?limit=10')
        if (articlesResponse.ok) {
          const articlesData = await articlesResponse.json()
          setArticles(articlesData.articles || [])
        }

        // Fetch automation status
        const statusResponse = await fetch('/api/auto/status')
        if (statusResponse.ok) {
          const statusData: AutoCollectionStatus = await statusResponse.json()
          setAutoCollectionStatus(statusData)
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleToggleAutoCollection = async (type: 'api' | 'rss') => {
    try {
      const isCurrentlyRunning = type === 'api' ? autoCollectionStatus.api_running : autoCollectionStatus.rss_running
      const endpoint = isCurrentlyRunning 
        ? (type === 'api' ? '/api/auto/stop_api' : '/api/auto/stop_rss')
        : (type === 'api' ? '/api/auto/start_api' : '/api/auto/start_rss')

      const response = await fetch(endpoint, { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          interval: 180  // Default interval of 180 seconds
        })
      })
      
      if (response.ok) {
        // Refresh status
        const statusResponse = await fetch('/api/auto/status')
        if (statusResponse.ok) {
          const statusData: AutoCollectionStatus = await statusResponse.json()
          setAutoCollectionStatus(statusData)
        }
      } else {
        console.error(`Failed to toggle ${type} collection:`, response.status, response.statusText)
      }
    } catch (error) {
      console.error(`Error toggling ${type} collection:`, error)
    }
  }

  const formatDateTime = (isoString: string | null) => {
    if (!isoString) return "N/A"
    const date = new Date(isoString)
    return date.toLocaleString('en-US', { 
      year: 'numeric', 
      month: 'numeric', 
      day: 'numeric', 
      hour: 'numeric', 
      minute: 'numeric', 
      second: 'numeric', 
      hour12: false 
    }) 
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator
              orientation="vertical"
              className="mr-2 data-[orientation=vertical]:h-4"
            />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem className="hidden md:block">
                  <BreadcrumbLink href="/dashboard">
                    News Reader Elite
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator className="hidden md:block" />
                <BreadcrumbItem>
                  <BreadcrumbPage>Dashboard</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>
        
        <div className="flex flex-1 flex-col gap-6 p-6 pt-2">
          {/* Welcome Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
              <p className="text-muted-foreground">
                Welcome to News Reader Elite - Monitor your news collection in real-time
              </p>
            </div>
            <Button className="gap-2" onClick={() => window.location.reload()}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>

          {/* Statistics Cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Database & File Counts</CardTitle>
                <Newspaper className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold flex items-baseline gap-1">
                  {stats?.database_count?.toLocaleString() || 0}
                  {stats && stats.api_new > 0 && (
                    <span className="text-xs text-muted-foreground ml-2">+ {stats.api_new} (API)</span>
                  )}
                  {stats && stats.rss_new > 0 && (
                    <span className="text-xs text-muted-foreground ml-1">+ {stats.rss_new} (RSS)</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mb-4">
                  Total articles in PostgreSQL
                </p>
                <div className="flex flex-col gap-2 mt-2">
                  <div className="flex justify-between items-baseline">
                    <span className="text-sm font-semibold">{stats?.mongodb_backup_count?.toLocaleString() || 0}</span>
                    <span className="text-xs text-muted-foreground">MongoDB</span>
                  </div>
                   <div className="flex justify-between items-baseline">
                    <span className="text-sm font-semibold">{stats?.total_json_file_count?.toLocaleString() || 0}</span>
                    <span className="text-xs text-muted-foreground">Local JSON Files</span>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">API Articles</CardTitle>
                <Globe className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold flex items-baseline gap-1">
                  {autoCollectionStatus.api_total?.toLocaleString() || 0}
                  {autoCollectionStatus.api_new > 0 && (
                    <span className="text-xs text-muted-foreground">+ {autoCollectionStatus.api_new}</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Last collected: {formatDateTime(stats?.last_api_collection_time)}
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">RSS Articles</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold flex items-baseline gap-1">
                  {autoCollectionStatus.rss_total?.toLocaleString() || 0}
                  {autoCollectionStatus.rss_new > 0 && (
                    <span className="text-xs text-muted-foreground">+ {autoCollectionStatus.rss_new}</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Last collected: {formatDateTime(stats?.last_rss_collection_time)}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Auto Collection Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Auto Collection Status
              </CardTitle>
              <CardDescription>
                Manage automatic news collection from APIs and RSS feeds
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Badge 
                  variant={autoCollectionStatus.api_error_occurred ? "destructive" : "secondary"}
                  className={`h-9 px-4 flex items-center justify-center min-w-[90px] ${
                    autoCollectionStatus.api_running && !autoCollectionStatus.api_error_occurred ? "bg-green-600 text-white" : ""
                  }`}
                >
                  {autoCollectionStatus.api_error_occurred ? "Error" : (autoCollectionStatus.api_running ? "Running" : "Stopped")}
                </Badge>
                <Button
                  variant={autoCollectionStatus.api_error_occurred ? "destructive" : (autoCollectionStatus.api_running ? "default" : "outline")}
                  size="sm"
                  onClick={() => handleToggleAutoCollection('api')}
                  className={`h-9 px-4 gap-2 min-w-[110px] ${
                    autoCollectionStatus.api_running && !autoCollectionStatus.api_error_occurred ? "bg-green-600 hover:bg-green-700 text-white" : ""
                  }`}
                >
                  {autoCollectionStatus.api_running && !autoCollectionStatus.api_error_occurred ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : null}
                  {autoCollectionStatus.api_running ? 'Stop' : 'Start'} API
                </Button>
              </div>
              
              <div className="flex items-center gap-2">
                <Badge 
                  variant={autoCollectionStatus.rss_error_occurred ? "destructive" : "secondary"}
                  className={`h-9 px-4 flex items-center justify-center min-w-[90px] ${
                    autoCollectionStatus.rss_running && !autoCollectionStatus.rss_error_occurred ? "bg-green-600 text-white" : ""
                  }`}
                >
                  {autoCollectionStatus.rss_error_occurred ? "Error" : (autoCollectionStatus.rss_running ? "Running" : "Stopped")}
                </Badge>
                <Button
                  variant={autoCollectionStatus.rss_error_occurred ? "destructive" : (autoCollectionStatus.rss_running ? "default" : "outline")}
                  size="sm"
                  onClick={() => handleToggleAutoCollection('rss')}
                  className={`h-9 px-4 gap-2 min-w-[110px] ${
                    autoCollectionStatus.rss_running && !autoCollectionStatus.rss_error_occurred ? "bg-green-600 hover:bg-green-700 text-white" : ""
                  }`}
                >
                  {autoCollectionStatus.rss_running && !autoCollectionStatus.rss_error_occurred ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : null}
                  {autoCollectionStatus.rss_running ? 'Stop' : 'Start'} RSS
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Latest Articles */}
          <Card className="flex-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Newspaper className="h-5 w-5" />
                Latest Articles
              </CardTitle>
              <CardDescription>
                Most recently collected news articles
              </CardDescription>
            </CardHeader>
            <CardContent className="max-h-[300px] overflow-y-auto">
              {loading ? (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-muted rounded w-1/2"></div>
                    </div>
                  ))}
                </div>
              ) : articles.length > 0 ? (
                <div className="space-y-4">
                  {articles.map((article, index) => (
                    <div key={index} className="border-b pb-4 last:border-b-0">
                      <h3 className="font-semibold line-clamp-2 text-sm mb-1">
                        <a 
                          href={article.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="hover:text-primary transition-colors"
                        >
                          {article.title}
                        </a>
                      </h3>
                      {article.description && (
                        <p className="text-muted-foreground text-xs line-clamp-2 mb-2">
                          {article.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline" className="text-xs">
                          {article.source_name || 'Unknown Source'}
                        </Badge>
                        <span>•</span>
                        <span>
                          {article.published_at ? 
                            new Date(article.published_at).toLocaleString('en-US', { 
                              year: 'numeric', 
                              month: 'numeric', 
                              day: 'numeric', 
                              hour: 'numeric', 
                              minute: 'numeric', 
                              second: 'numeric', 
                              hour12: false 
                            }) : 
                            'No date'
                          }
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Newspaper className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No articles found. Start collecting news to see them here.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
