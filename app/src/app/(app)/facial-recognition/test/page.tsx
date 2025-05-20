"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Upload, Play, FileVideo, Users, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"

export default function TestModelPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [framesProcessed, setFramesProcessed] = useState(0)
  const [totalFrames, setTotalFrames] = useState(0)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [taskId, setTaskId] = useState<string | null>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type.startsWith('video/')) {
      setSelectedFile(file)
      setError(null)
      setResults(null)
    } else {
      setError('Please select a valid video file')
    }
  }, [])

  const pollTaskStatus = async (taskId: string) => {
    try {
      const response = await fetch(`/api/training/test/${taskId}`)
      if (!response.ok) {
        throw new Error('Failed to get task status')
      }
      
      const data = await response.json()
      
      // Update progress
      setProcessingProgress(data.progress)
      setFramesProcessed(data.frames_processed)
      setTotalFrames(data.total_frames)
      
      // Check if task is completed
      if (data.status === 'completed') {
        setResults(data.results)
        setIsProcessing(false)
        // Stop polling
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current)
          pollIntervalRef.current = null
        }
      } else if (data.status === 'failed') {
        setError(data.error || 'Test failed')
        setIsProcessing(false)
        // Stop polling
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current)
          pollIntervalRef.current = null
        }
      }
    } catch (err) {
      console.error('Error polling task status:', err)
      setError('Failed to get task status')
      setIsProcessing(false)
      // Stop polling on error
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setIsProcessing(true)
    setError(null)
    setResults(null)
    setProcessingProgress(0)
    setFramesProcessed(0)
    setTotalFrames(0)

    try {
      // First, upload the video
      const uploadFormData = new FormData()
      uploadFormData.append('video_file', selectedFile)

      console.log('[DEBUG] Starting upload:', selectedFile.name, 'Size:', selectedFile.size)

      const uploadResponse = await fetch('/api/videos/upload', {
        method: 'POST',
        body: uploadFormData,
      })

      console.log('[DEBUG] Upload response status:', uploadResponse.status)

      if (!uploadResponse.ok) {
        let errorDetail = 'Failed to upload video'
        try {
          const errorText = await uploadResponse.text()
          console.error('[DEBUG] Error response text:', errorText)
          try {
            const errorData = JSON.parse(errorText)
            errorDetail = errorData.detail || errorData.error || errorData.message || errorDetail
          } catch {
            // If it's not JSON, use the text directly
            if (errorText) {
              errorDetail = errorText
            }
          }
        } catch (e) {
          console.error('[DEBUG] Failed to read error response:', e)
        }
        throw new Error(errorDetail)
      }

      const uploadData = await uploadResponse.json()
      const videoId = uploadData.upload_id

      console.log('[DEBUG] Upload response data:', uploadData)
      console.log('[DEBUG] Video ID:', videoId)
      
      if (!videoId) {
        throw new Error('No upload ID received from server')
      }

      setIsUploading(false)

      // Now start the test using form data
      const testFormData = new FormData()
      testFormData.append('upload_id', videoId)
      testFormData.append('use_latest', 'true')

      console.log('[DEBUG] Starting test with upload_id:', videoId)
      console.log('[DEBUG] FormData content:', [...testFormData.entries()])
      console.log('[DEBUG] Request URL:', '/api/training/test')

      // First, try the debug endpoint
      const debugResponse = await fetch('/api/training/test/debug', {
        method: 'POST',
        body: testFormData,
      })
      
      if (debugResponse.ok) {
        const debugData = await debugResponse.json()
        console.log('[DEBUG] Debug endpoint response:', debugData)
      }

      const testResponse = await fetch('/api/training/test', {
        method: 'POST',
        body: testFormData,
        headers: {
          // Remove this if it causes issues - FormData needs automatic boundary
          // 'Content-Type': 'multipart/form-data'
        }
      })
      
      console.log('[DEBUG] Test response status:', testResponse.status)
      console.log('[DEBUG] Test response headers:', testResponse.headers)

      if (!testResponse.ok) {
        let errorDetail = 'Failed to start test'
        try {
          const errorText = await testResponse.text()
          console.error('[DEBUG] Error response text:', errorText)
          try {
            const errorData = JSON.parse(errorText)
            errorDetail = errorData.detail || errorData.error || errorData.message || errorDetail
          } catch {
            // If it's not JSON, use the text directly
            if (errorText) {
              errorDetail = errorText
            }
          }
        } catch (e) {
          console.error('[DEBUG] Failed to read error response:', e)
        }
        throw new Error(errorDetail)
      }

      const testData = await testResponse.json()
      const taskId = testData.task_id

      console.log('[DEBUG] Test started with task ID:', taskId)
      setTaskId(taskId)

      // Start polling for progress updates
      pollIntervalRef.current = setInterval(() => {
        pollTaskStatus(taskId)
      }, 1000) // Poll every second

    } catch (err) {
      console.error('Error:', err)
      setError(err instanceof Error ? err.message : 'An error occurred')
      setIsUploading(false)
      setIsProcessing(false)
    }
  }

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  return (
    <div className="container mx-auto py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Test Employee Detection Model</h1>
        <p className="text-muted-foreground mt-2">
          Upload a video to test the trained employee detection model
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Test Video</CardTitle>
            <CardDescription>
              Select a video file to test employee detection
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="video-upload"
                />
                <label
                  htmlFor="video-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <Upload className="h-10 w-10 text-gray-400 mb-2" />
                  <span className="text-sm text-gray-600">
                    Click to select video or drag and drop
                  </span>
                </label>
              </div>

              {selectedFile && (
                <div className="flex items-center space-x-2 p-3 bg-muted rounded-lg">
                  <FileVideo className="h-5 w-5" />
                  <span className="text-sm truncate flex-1">{selectedFile.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
              )}

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button
                onClick={handleUpload}
                disabled={!selectedFile || isProcessing}
                className="w-full"
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Test Model
                  </>
                )}
              </Button>

              {isUploading && (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Uploading video...</p>
                  <Progress value={uploadProgress} className="w-full" />
                </div>
              )}

              {isProcessing && !isUploading && (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Processing frames: {framesProcessed} / {totalFrames}
                  </p>
                  <Progress value={processingProgress} className="w-full" />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Results Section */}
        <Card>
          <CardHeader>
            <CardTitle>Test Results</CardTitle>
            <CardDescription>
              Employee detection results from the uploaded video
            </CardDescription>
          </CardHeader>
          <CardContent>
            {results ? (
              <div className="space-y-4">
                {results.success ? (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <div className="text-2xl font-bold">{results.total_frames}</div>
                        <div className="text-sm text-muted-foreground">Total Frames</div>
                      </div>
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <div className="text-2xl font-bold">{results.unique_employees?.length || 0}</div>
                        <div className="text-sm text-muted-foreground">Employees Detected</div>
                      </div>
                    </div>

                    {results.unique_employees && results.unique_employees.length > 0 ? (
                      <div>
                        <h3 className="font-semibold mb-2">Detected Employees</h3>
                        <div className="flex flex-wrap gap-2">
                          {results.unique_employees.map((employee: string) => (
                            <Badge key={employee} variant="secondary">
                              <Users className="h-3 w-3 mr-1" />
                              {employee}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <Alert className="mt-4">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          No employees detected in the video. This could mean:
                          <ul className="list-disc ml-6 mt-2">
                            <li>The video doesn't contain faces from trained employees</li>
                            <li>The confidence threshold needs adjustment</li>
                            <li>The model needs more training data</li>
                          </ul>
                        </AlertDescription>
                      </Alert>
                    )}

                    {results.summary && (
                      <div>
                        <h3 className="font-semibold mb-2">Detection Summary</h3>
                        <div className="space-y-1 text-sm">
                          <div>Total detections: {results.summary.total_detections}</div>
                          <div>Frames with detections: {results.summary.frames_with_detections}</div>
                          <div>Average confidence: {(results.summary.average_confidence * 100).toFixed(1)}%</div>
                        </div>
                      </div>
                    )}

                    {results.detections && results.detections.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-2">Sample Detections</h3>
                        <div className="max-h-40 overflow-y-auto text-xs space-y-1">
                          {results.detections.slice(0, 10).map((detection: any, idx: number) => (
                            <div key={idx} className="p-1 bg-muted rounded">
                              Frame {detection.frame}: {detection.employee_id} ({(detection.confidence * 100).toFixed(1)}%)
                            </div>
                          ))}
                          {results.detections.length > 10 && (
                            <div className="text-muted-foreground">
                              ... and {results.detections.length - 10} more detections
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{results.error}</AlertDescription>
                  </Alert>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <FileVideo className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No results yet. Upload a video to test the model.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}