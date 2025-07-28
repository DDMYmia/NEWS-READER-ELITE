"use client"

import * as React from "react"
import {
  AudioWaveform,
  BookOpen,
  Bot,
  Command,
  Frame,
  GalleryVerticalEnd,
  Map,
  PieChart,
  Settings2,
  SquareTerminal,
  Newspaper,
  Database,
  Globe,
  Activity,
  BarChart3,
  Rss,
  Zap,
  User,
} from "lucide-react"

import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"

// News Reader Elite application data
const data = {
  user: {
    name: "News Admin",
    email: "admin@newsreader.com",
    avatar: "/avatars/admin.jpg",
  },
  teams: [
    {
      name: "News Reader Elite",
      logo: Newspaper,
      plan: "Professional",
    },
    {
      name: "Data Analytics",
      logo: BarChart3,
      plan: "Enterprise",
    },
    {
      name: "API Management",
      logo: Zap,
      plan: "Premium",
    },
  ],
  navMain: [
    {
      title: "Dashboard",
      url: "/dashboard",
      icon: SquareTerminal,
      isActive: true,
      items: [
        {
          title: "Overview",
          url: "/dashboard",
        },
        {
          title: "Real-time Monitor",
          url: "/dashboard/monitor",
        },
        {
          title: "Statistics",
          url: "/dashboard/stats",
        },
      ],
    },
    {
      title: "News Collection",
      url: "#",
      icon: Newspaper,
      items: [
        {
          title: "Latest Articles",
          url: "/news/latest",
        },
        {
          title: "API Sources",
          url: "/news/api-sources",
        },
        {
          title: "RSS Feeds",
          url: "/news/rss-feeds",
        },
      ],
    },
    {
      title: "Data Sources",
      url: "#",
      icon: Database,
      items: [
        {
          title: "NewsAPI.ai",
          url: "/sources/newsapi-ai",
        },
        {
          title: "TheNewsAPI",
          url: "/sources/thenewsapi",
        },
        {
          title: "NewsData.io",
          url: "/sources/newsdata",
        },
        {
          title: "Tiingo",
          url: "/sources/tiingo",
        },
        {
          title: "AlphaVantage",
          url: "/sources/alphavantage",
        },
      ],
    },
    {
      title: "Automation",
      url: "#",
      icon: Bot,
      items: [
        {
          title: "Auto Collection",
          url: "/automation/collection",
        },
        {
          title: "Scheduled Tasks",
          url: "/automation/schedules",
        },
        {
          title: "Status Monitor",
          url: "/automation/status",
        },
      ],
    },
    {
      title: "Analytics",
      url: "#",
      icon: BarChart3,
      items: [
        {
          title: "Collection Stats",
          url: "/analytics/collection",
        },
        {
          title: "Source Performance",
          url: "/analytics/sources",
        },
        {
          title: "Trends",
          url: "/analytics/trends",
        },
      ],
    },
    {
      title: "Settings",
      url: "#",
      icon: Settings2,
      items: [
        {
          title: "API Keys",
          url: "/settings/api-keys",
        },
        {
          title: "Database",
          url: "/settings/database",
        },
        {
          title: "Notifications",
          url: "/settings/notifications",
        },
        {
          title: "General",
          url: "/settings/general",
        },
      ],
    },
  ],
  projects: [
    {
      name: "Live RSS Collection",
      url: "/projects/rss-live",
      icon: Rss,
    },
    {
      name: "API Data Pipeline",
      url: "/projects/api-pipeline",
      icon: Activity,
    },
    {
      name: "Global News Monitor",
      url: "/projects/global-monitor",
      icon: Globe,
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
