import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, Brain, Shield, Zap, Users, FileText, Activity } from "lucide-react"
import Link from "next/link"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-gray-900/80">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-white">MediDiagnose</span>
          </div>
          <Link href="/patients/records">
            <Button>
              Get Started
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <Badge variant="secondary" className="mb-4">
            AI-Powered Medical Diagnosis
          </Badge>
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-6 max-w-4xl mx-auto">
            Revolutionary Medical Diagnosis Platform
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
            Harness the power of artificial intelligence to enhance medical diagnosis accuracy, streamline patient care,
            and improve healthcare outcomes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/patients/records">
              <Button size="lg" className="w-full sm:w-auto">
                Start Diagnosis
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </Link>
            <Link href="/diagnosis">
              <Button variant="outline" size="lg" className="w-full sm:w-auto bg-transparent">
                Upload X-Ray
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 bg-white/50 dark:bg-gray-800/50">
        <div className="container mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">Advanced Medical Technology</h2>
            <p className="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Our platform combines cutting-edge AI with intuitive design to revolutionize medical diagnosis
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <Brain className="w-10 h-10 text-blue-600 mb-2" />
                <CardTitle>AI-Powered Analysis</CardTitle>
                <CardDescription>
                  Advanced machine learning algorithms analyze medical images with unprecedented accuracy
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <Shield className="w-10 h-10 text-green-600 mb-2" />
                <CardTitle>HIPAA Compliant</CardTitle>
                <CardDescription>
                  Enterprise-grade security ensures patient data privacy and regulatory compliance
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <Zap className="w-10 h-10 text-yellow-600 mb-2" />
                <CardTitle>Instant Results</CardTitle>
                <CardDescription>
                  Get diagnostic insights in seconds, not hours, accelerating patient care
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 px-4">
        <div className="container mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">How It Works</h2>
            <p className="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Simple, efficient workflow designed for healthcare professionals
            </p>
          </div>
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Register Patient</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">Add patient information and medical history</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Upload Images</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                Upload X-rays, CT scans, or other medical images
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">AI Analysis</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                Our AI analyzes images and provides diagnostic insights
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Activity className="w-8 h-8 text-orange-600" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Get Results</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                Review detailed diagnosis and treatment recommendations
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 bg-blue-600 dark:bg-blue-700">
        <div className="container mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Transform Your Practice?</h2>
          <p className="text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of healthcare professionals who trust MediDiagnose for accurate, fast, and reliable medical
            diagnosis.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/patients/records">
              <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                Start Free Trial
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </Link>
            <Link href="/diagnosis">
              <Button
                size="lg"
                variant="outline"
                className="w-full sm:w-auto border-white text-white hover:bg-white hover:text-blue-600 bg-transparent"
              >
                Schedule Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 px-4">
        <div className="container mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-semibold">MediDiagnose</span>
          </div>
          <p className="text-gray-400">© 2025 MediDiagnose. All rights reserved. | Privacy Policy | Terms of Service</p>
        </div>
      </footer>
    </div>
  )
}
