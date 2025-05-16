"use client"

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'

export function DebugTest() {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const testAPI = async () => {
    setLoading(true)
    setError(null)
    setData(null)
    
    try {
      const response = await fetch('/api/identity-groups')
      console.log('Response status:', response.status)
      console.log('Response headers:', response.headers)
      
      if (!response.ok) {
        const text = await response.text()
        console.error('Error response:', text)
        setError(`Error ${response.status}: ${text}`)
        return
      }
      
      const json = await response.json()
      console.log('Response data:', json)
      setData(json)
    } catch (err: any) {
      console.error('Fetch error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 border rounded">
      <h3 className="font-bold mb-2">API Debug Test</h3>
      <Button onClick={testAPI} disabled={loading}>
        {loading ? 'Testing...' : 'Test API'}
      </Button>
      
      {error && (
        <div className="mt-4 p-2 bg-red-100 text-red-700 rounded">
          Error: {error}
        </div>
      )}
      
      {data && (
        <div className="mt-4">
          <pre className="p-2 bg-gray-100 rounded overflow-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}