"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Upload, Camera, Stethoscope, Brain, AlertTriangle, CheckCircle, Download } from "lucide-react"
import Image from "next/image"
import { useQuery } from "convex/react"
import { api } from "@/convex/_generated/api"

export default function DiagnosisPage() {
  const [selectedPatient, setSelectedPatient] = useState("")
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)

  // Fetch patients from Convex database
  const patients = useQuery(api.getPatients.default) ?? []

  // Get selected patient details
  const selectedPatientData = patients.find(p => p._id === selectedPatient)

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setUploadedImage(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleAnalyze = async () => {
    if (!selectedPatient || !uploadedImage) return;

    setIsAnalyzing(true);
    setAnalysisComplete(false);
    setAnalysisProgress(0);

    try {
      // Convert base64 to blob
      const response = await fetch(uploadedImage);
      const blob = await response.blob();
      const file = new File([blob], 'xray.jpg', { type: 'image/jpeg' });
      
      // Update progress
      setAnalysisProgress(20);
      
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      // Call backend API
      setAnalysisProgress(40);
      const apiResponse = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        body: formData,
      });
      
      if (!apiResponse.ok) {
        throw new Error(`Analysis failed: ${apiResponse.status}`);
      }
      
      const result = await apiResponse.json();
      setAnalysisProgress(80);
      
      // Update with real results
      if (result && result.length > 0) {
        // Find the highest confidence prediction
        const topPrediction = result.reduce((max: any, current: any) => 
          (current.probability > max.probability) ? current : max
        );
        
        // Get top 3 predictions for findings
        const topPredictions = result
          .sort((a: any, b: any) => b.probability - a.probability)
          .slice(0, 3);
        
        // Map prediction to diagnosis format
        setDiagnosis({
          condition: topPrediction.class_name,
          confidence: Math.round(topPrediction.probability * 100),
          severity: topPrediction.probability > 0.7 ? 'High' : 
                   topPrediction.probability > 0.4 ? 'Moderate' : 'Low',
          findings: topPredictions.map((pred: any) => 
            `${pred.class_name}: ${Math.round(pred.probability * 100)}% confidence`
          ),
          recommendations: [
            'Consult with a radiologist for detailed analysis',
            'Consider additional imaging if symptoms persist',
            'Follow up as clinically indicated',
            'Review patient history and symptoms'
          ]
        });
      }
      
      setAnalysisProgress(100);
      setAnalysisComplete(true);
    } catch (error) {
      console.error('Analysis error:', error);
      // Show error state with fallback data
      setDiagnosis({
        condition: "Analysis Error",
        confidence: 0,
        severity: "Unknown",
        findings: [
          "Unable to connect to AI analysis service",
          "Please check backend connection",
          "Retry analysis or contact support"
        ],
        recommendations: [
          "Ensure backend server is running",
          "Check network connectivity",
          "Contact technical support if issue persists"
        ]
      });
      setAnalysisComplete(true);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveReport = () => {
    if (!selectedPatientData || !diagnosis.condition) return;

    try {
      // Create a simple text report for now to avoid jsPDF issues
      const reportContent = `
MEDICAL DIAGNOSIS REPORT
Generated on: ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}

PATIENT INFORMATION
Name: ${selectedPatientData.firstName} ${selectedPatientData.lastName}
Date of Birth: ${selectedPatientData.dateOfBirth}
Gender: ${selectedPatientData.gender}
Phone: ${selectedPatientData.phone}
Email: ${selectedPatientData.email}
Blood Type: ${selectedPatientData.bloodType}
Insurance: ${selectedPatientData.insurance} (ID: ${selectedPatientData.insuranceId})

AI ANALYSIS RESULTS
Primary Diagnosis: ${diagnosis.condition}
Confidence: ${diagnosis.confidence}%
Severity: ${diagnosis.severity}

Key Findings:
${diagnosis.findings.map(finding => `• ${finding}`).join('\n')}

Treatment Recommendations:
${diagnosis.recommendations.map((rec, index) => `${index + 1}. ${rec}`).join('\n')}

MEDICAL DISCLAIMER
This system provides automated results that may not always be accurate or complete. Users are strongly advised to exercise caution, apply their own knowledge, and critically evaluate all outputs. Do not rely solely on the system for important decisions. Always cross-check results and use professional judgment when interpreting the information provided.
      `;

      // Create and download text file
      const blob = new Blob([reportContent], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Medical_Report_${selectedPatientData.firstName}_${selectedPatientData.lastName}_${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Error generating report. Please try again.');
    }
  };

  const [diagnosis, setDiagnosis] = useState({
    condition: "",
    confidence: 0,
    severity: "",
    findings: [] as string[],
    recommendations: [] as string[],
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <Stethoscope className="w-6 h-6 text-blue-600" />
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AI Diagnosis</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle>Medical Image Upload</CardTitle>
            <CardDescription>Upload X-ray, CT scan, or other medical images for AI analysis</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Patient Selection */}
            <div className="space-y-2">
              <Label>Select Patient</Label>
              <Select value={selectedPatient} onValueChange={setSelectedPatient}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a patient" />
                </SelectTrigger>
                <SelectContent>
                  {patients.map((patient) => (
                    <SelectItem key={patient._id} value={patient._id}>
                      {patient.firstName} {patient.lastName} (DOB: {patient.dateOfBirth})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Image Upload */}
            <div className="space-y-2">
              <Label>Medical Image</Label>
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                {uploadedImage ? (
                  <div className="space-y-4">
                    <Image
                      src={uploadedImage || "/placeholder.svg"}
                      alt="Uploaded medical image"
                      width={300}
                      height={200}
                      className="mx-auto rounded-lg"
                    />
                    <Button variant="outline" onClick={() => setUploadedImage(null)}>
                      Remove Image
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex justify-center space-x-4">
                      <Upload className="w-12 h-12 text-gray-400" />
                      <Camera className="w-12 h-12 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-lg font-medium text-gray-900 dark:text-white">Upload Medical Image</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Drag and drop or click to select</p>
                    </div>
                    <div className="flex justify-center space-x-2">
                      <Button variant="outline" asChild>
                        <label htmlFor="image-upload" className="cursor-pointer">
                          <Upload className="w-4 h-4 mr-2" />
                          Upload File
                        </label>
                      </Button>
                      <Button variant="outline">
                        <Camera className="w-4 h-4 mr-2" />
                        Take Photo
                      </Button>
                    </div>
                    <input
                      id="image-upload"
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Analysis Button */}
            <Button
              onClick={handleAnalyze}
              disabled={!selectedPatient || !uploadedImage || isAnalyzing}
              className="w-full"
            >
              {isAnalyzing ? (
                <>
                  <Brain className="w-4 h-4 mr-2 animate-pulse" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Brain className="w-4 h-4 mr-2" />
                  Start AI Analysis
                </>
              )}
            </Button>

            {/* Progress Bar */}
            {isAnalyzing && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>AI Analysis Progress</span>
                  <span>{analysisProgress}%</span>
                </div>
                <Progress value={analysisProgress} className="w-full" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Section */}
        <Card>
          <CardHeader>
            <CardTitle>Diagnosis Results</CardTitle>
            <CardDescription>AI-powered medical image analysis results</CardDescription>
          </CardHeader>
          <CardContent>
            {!analysisComplete ? (
              <div className="text-center py-12">
                <Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Upload an image and select a patient to start diagnosis
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Primary Diagnosis */}
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">Primary Diagnosis</h3>
                    <Badge variant="secondary">{diagnosis.confidence}% Confidence</Badge>
                  </div>
                  <p className="text-2xl font-bold text-blue-800 dark:text-blue-200">{diagnosis.condition}</p>
                  <p className="text-sm text-blue-600 dark:text-blue-300">Severity: {diagnosis.severity}</p>
                </div>

                {/* Key Findings */}
                <div>
                  <h4 className="font-semibold mb-3 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2 text-orange-500" />
                    Key Findings
                  </h4>
                  <ul className="space-y-2">
                    {diagnosis.findings.map((finding, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0" />
                        <span className="text-sm text-gray-700 dark:text-gray-300">{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Recommendations */}
                <div>
                  <h4 className="font-semibold mb-3 flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    Treatment Recommendations
                  </h4>
                  <ul className="space-y-2">
                    {diagnosis.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                        <span className="text-sm text-gray-700 dark:text-gray-300">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-2 pt-4">
                  <Button 
                    variant="outline" 
                    className="flex-1 bg-transparent"
                    onClick={handleSaveReport}
                    disabled={!selectedPatientData || !analysisComplete}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Save Report
                  </Button>
                  <Button className="flex-1">Share with Doctor</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Disclaimer */}
      <Card className="border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20 dark:border-yellow-800">
        <CardContent className="p-4">
          <div className="flex items-start space-x-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-yellow-800 dark:text-yellow-200">
              <p className="font-semibold mb-1">Medical Disclaimer</p>
              <p>
              This system provides automated results that may not always be accurate or complete. Users are strongly advised to exercise caution,
              apply their own knowledge, and critically evaluate all outputs. Do not rely solely on the system for important decisions.
              Always cross-check results and use professional judgment when interpreting the information provided.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
