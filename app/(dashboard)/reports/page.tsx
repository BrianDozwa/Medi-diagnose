"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { BarChart3, TrendingUp, Users, Activity, Download, Calendar, AlertTriangle, CheckCircle } from "lucide-react"

export default function ReportsPage() {
  const mockReports = [
    {
      title: "Patient Volume Report",
      description: "Monthly patient admission and discharge statistics",
      value: "1,247",
      change: "+12%",
      trend: "up",
      period: "Last 30 days",
    },
    {
      title: "Diagnosis Accuracy",
      description: "AI diagnosis accuracy compared to physician diagnosis",
      value: "94.2%",
      change: "+2.1%",
      trend: "up",
      period: "Last quarter",
    },
    {
      title: "System Usage",
      description: "Active users and system utilization metrics",
      value: "89%",
      change: "-3%",
      trend: "down",
      period: "This week",
    },
    {
      title: "Response Time",
      description: "Average diagnosis processing time",
      value: "2.3s",
      change: "-0.5s",
      trend: "up",
      period: "Last 7 days",
    },
  ]

  const departmentStats = [
    { name: "Emergency", patients: 342, utilization: 87 },
    { name: "Cardiology", patients: 156, utilization: 72 },
    { name: "Radiology", patients: 289, utilization: 94 },
    { name: "Pediatrics", patients: 198, utilization: 65 },
    { name: "Surgery", patients: 124, utilization: 78 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">System Reports</h1>
          <p className="text-gray-500 dark:text-gray-400">Analytics and performance metrics</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Calendar className="w-4 h-4 mr-2" />
            Date Range
          </Button>
          <Button>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {mockReports.map((report, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{report.title}</CardTitle>
              <div className="h-4 w-4">
                {report.trend === "up" ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <Activity className="h-4 w-4 text-red-600" />
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{report.value}</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <Badge
                  variant={report.trend === "up" ? "default" : "secondary"}
                  className={report.trend === "up" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}
                >
                  {report.change}
                </Badge>
                <span>{report.period}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">{report.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Department Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Department Performance</CardTitle>
          <CardDescription>Patient volume and resource utilization by department</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {departmentStats.map((dept, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{dept.name}</h3>
                    <div className="text-sm text-gray-500">{dept.patients} patients</div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Progress value={dept.utilization} className="flex-1" />
                    <span className="text-sm font-medium">{dept.utilization}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>System Alerts</CardTitle>
            <CardDescription>Recent system notifications and alerts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3 p-3 border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20">
                <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
                <div>
                  <p className="font-medium text-red-800 dark:text-red-200">High System Load</p>
                  <p className="text-sm text-red-600 dark:text-red-300">Server utilization at 89% - consider scaling</p>
                  <p className="text-xs text-red-500 mt-1">2 hours ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-3 p-3 border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20">
                <AlertTriangle className="w-5 h-5 text-yellow-500 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-800 dark:text-yellow-200">Backup Completed</p>
                  <p className="text-sm text-yellow-600 dark:text-yellow-300">Daily backup completed successfully</p>
                  <p className="text-xs text-yellow-500 mt-1">6 hours ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-3 p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20">
                <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                <div>
                  <p className="font-medium text-green-800 dark:text-green-200">System Update</p>
                  <p className="text-sm text-green-600 dark:text-green-300">AI model updated to version 2.1.4</p>
                  <p className="text-xs text-green-500 mt-1">1 day ago</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
            <CardDescription>Key performance indicators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Users className="w-5 h-5 text-blue-600" />
                  <span className="font-medium">Active Users</span>
                </div>
                <span className="text-2xl font-bold text-blue-600">47</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Activity className="w-5 h-5 text-green-600" />
                  <span className="font-medium">Diagnoses Today</span>
                </div>
                <span className="text-2xl font-bold text-green-600">156</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                  <span className="font-medium">Avg. Accuracy</span>
                </div>
                <span className="text-2xl font-bold text-purple-600">94.2%</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-orange-600" />
                  <span className="font-medium">Uptime</span>
                </div>
                <span className="text-2xl font-bold text-orange-600">99.9%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
