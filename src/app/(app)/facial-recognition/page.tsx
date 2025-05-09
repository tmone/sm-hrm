
'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Camera, UserPlus, Upload, ListChecks, RotateCcw, CheckCircle, AlertCircle, Clock, XCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { mockEmployees } from '@/lib/data';
import type { Employee } from '@/types';
import Image from 'next/image';
import { cn } from '@/lib/utils';

interface RegisteredFace {
  id: string;
  employeeName: string;
  employeeId: string;
  imageUrl?: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  registeredDate: string;
}

const mockRegisteredFacesData: RegisteredFace[] = [
  { id: 'face001', employeeId: 'emp001', employeeName: 'Alice Smith', status: 'Approved', registeredDate: '2024-07-20', imageUrl: 'https://picsum.photos/seed/face_alice/80/80' },
  { id: 'face002', employeeId: 'emp002', employeeName: 'Bob Johnson', status: 'Pending', registeredDate: '2024-07-25', imageUrl: 'https://picsum.photos/seed/face_bob/80/80' },
  { id: 'face003', employeeId: 'emp004', employeeName: 'David Brown', status: 'Rejected', registeredDate: '2024-07-22', imageUrl: 'https://picsum.photos/seed/face_david/80/80' },
];


export default function FacialRecognitionPage() {
  const { toast } = useToast();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hasCameraPermission, setHasCameraPermission] = useState<boolean | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [selectedEmployee, setSelectedEmployee] = useState<string>('');
  const streamRef = useRef<MediaStream | null>(null);
  const [registeredFaces, setRegisteredFaces] = useState<RegisteredFace[]>(mockRegisteredFacesData);

  const stopCameraStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    const getCameraPermission = async () => {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (!isMounted) return;
        console.error('getUserMedia is not supported');
        setHasCameraPermission(false);
        toast({
          variant: 'destructive',
          title: 'Camera Not Supported',
          description: 'Your browser does not support camera access or it is not available.',
        });
        return;
      }
      try {
        const cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (!isMounted) {
          cameraStream.getTracks().forEach(track => track.stop());
          return;
        }
        streamRef.current = cameraStream;
        setHasCameraPermission(true);
        if (videoRef.current) {
          videoRef.current.srcObject = cameraStream;
        }
      } catch (error) {
        if (!isMounted) return;
        console.error('Error accessing camera:', error);
        setHasCameraPermission(false);
        toast({
          variant: 'destructive',
          title: 'Camera Access Denied',
          description: 'Please enable camera permissions in your browser settings to use this feature.',
        });
      }
    };

    getCameraPermission();

    return () => {
      isMounted = false;
      stopCameraStream();
    };
  }, [stopCameraStream, toast]);

  const handleCapture = () => {
    if (videoRef.current && canvasRef.current && videoRef.current.readyState >= videoRef.current.HAVE_METADATA) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext('2d');
      if (context) {
        // Flip the image horizontally if the camera is mirrored
        // context.translate(canvas.width, 0);
        // context.scale(-1, 1);
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageDataUrl = canvas.toDataURL('image/png');
        setCapturedImage(imageDataUrl);
      }
    } else {
      toast({ variant: 'destructive', title: 'Camera Not Ready', description: 'Please wait for the camera feed to load or ensure it is active.'});
    }
  };

  const handleRetake = () => {
    setCapturedImage(null);
  };

  const handleSubmit = () => {
    if (!capturedImage) {
      toast({ variant: 'destructive', title: 'No Image Captured', description: 'Please capture an image first.' });
      return;
    }
    if (!selectedEmployee) {
      toast({ variant: 'destructive', title: 'No Employee Selected', description: 'Please select an employee.' });
      return;
    }
    
    const employee = mockEmployees.find(e => e.id === selectedEmployee);
    toast({
      title: 'Face Registration Submitted',
      description: `Image for ${employee?.name || 'selected employee'} submitted for approval.`,
    });
    
    const newFace: RegisteredFace = {
        id: `face${Date.now()}`,
        employeeId: selectedEmployee,
        employeeName: employee?.name || 'Unknown Employee',
        status: 'Pending',
        registeredDate: new Date().toISOString().split('T')[0],
        imageUrl: capturedImage, 
    };
    setRegisteredFaces(prev => [newFace, ...prev]);

    setCapturedImage(null);
    setSelectedEmployee('');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Face Registration</h1>
          <p className="text-muted-foreground">Register employee faces for facial recognition attendance.</p>
        </div>
      </div>

      <Card className="shadow-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><UserPlus className="h-5 w-5 text-primary" /> Register New Face</CardTitle>
          <CardDescription>Capture and submit an employee&apos;s facial image.</CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-6 p-6">
          <div className="space-y-4">
            <Label>Camera Feed</Label>
            <div className="aspect-video w-full bg-muted rounded-md overflow-hidden border relative">
              <video ref={videoRef} className="w-full h-full object-cover" autoPlay muted playsInline />
              {hasCameraPermission === false && (
                <div className="absolute inset-0 flex items-center justify-center bg-background/80 p-4">
                  <Alert variant="destructive" className="w-full max-w-sm">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Camera Access Required</AlertTitle>
                    <AlertDescription>
                      Please allow camera access in your browser. You may need to reset site permissions.
                    </AlertDescription>
                  </Alert>
                </div>
              )}
              {hasCameraPermission === null && (
                 <div className="absolute inset-0 flex items-center justify-center bg-background/80 p-4">
                  <Alert className="w-full max-w-sm">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Checking Camera...</AlertTitle>
                    <AlertDescription>
                      Attempting to access camera. Grant permission if prompted.
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </div>
            <canvas ref={canvasRef} className="hidden"></canvas>
          </div>
          <div className="space-y-4">
            <Label>Captured Image</Label>
            <div className="aspect-video w-full bg-muted rounded-md overflow-hidden border flex items-center justify-center">
              {capturedImage ? (
                <Image src={capturedImage} alt="Captured face" width={300} height={225} className="object-contain max-h-full max-w-full" data-ai-hint="person face" />
              ) : (
                <p className="text-muted-foreground text-center p-4">No image captured yet. <br/> Use the camera feed to capture an image.</p>
              )}
            </div>
          </div>

          <div className="md:col-span-2 space-y-4">
             <div className="flex flex-col sm:flex-row gap-4">
              <Button onClick={handleCapture} disabled={hasCameraPermission !== true || !!capturedImage} className="w-full shadow-md">
                <Camera className="mr-2 h-5 w-5" /> Capture Image
              </Button>
              <Button onClick={handleRetake} disabled={!capturedImage} variant="outline" className="w-full shadow-md">
                <RotateCcw className="mr-2 h-5 w-5" /> Retake
              </Button>
            </div>

            <div>
              <Label htmlFor="employee-select">Select Employee</Label>
              <Select value={selectedEmployee} onValueChange={setSelectedEmployee} disabled={!capturedImage}>
                <SelectTrigger id="employee-select">
                  <SelectValue placeholder="Select employee to register" />
                </SelectTrigger>
                <SelectContent>
                  {mockEmployees.filter(e => e.status === 'Active').map(emp => (
                    <SelectItem key={emp.id} value={emp.id}>{emp.name} ({emp.id})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button onClick={handleSubmit} disabled={!capturedImage || !selectedEmployee} className="w-full shadow-md">
              <Upload className="mr-2 h-5 w-5" /> Submit for Approval
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><ListChecks className="h-5 w-5 text-primary" /> Registered Faces</CardTitle>
          <CardDescription>List of faces currently in the system and their approval status.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            {registeredFaces.length > 0 ? (
              <ul className="divide-y divide-border">
                {registeredFaces.map(face => (
                  <li key={face.id} className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 hover:bg-muted/50">
                    <div className="flex items-center gap-3 flex-grow">
                      {face.imageUrl && (
                        <Image 
                          src={face.imageUrl} 
                          alt={`${face.employeeName}'s face`} 
                          width={48} 
                          height={48} 
                          className="rounded-full object-cover aspect-square border"
                          data-ai-hint="person face"
                        />
                      )}
                      <div>
                        <p className="font-semibold text-sm sm:text-base">{face.employeeName}</p>
                        <p className="text-xs text-muted-foreground">ID: {face.employeeId} &bull; Registered: {face.registeredDate}</p>
                      </div>
                    </div>
                    <Badge
                      variant={
                        face.status === 'Approved' ? 'default' :
                        face.status === 'Pending' ? 'outline' :
                        'destructive'
                      }
                      className={cn(
                        "whitespace-nowrap text-xs mt-2 sm:mt-0",
                        face.status === 'Approved' && 'bg-green-500/20 text-green-700 dark:bg-green-500/30 dark:text-green-400 border-green-500/30',
                        face.status === 'Pending' && 'bg-yellow-500/20 text-yellow-700 dark:bg-yellow-500/30 dark:text-yellow-400 border-yellow-500/30',
                        face.status === 'Rejected' && 'bg-red-500/20 text-red-700 dark:bg-red-500/30 dark:text-red-400 border-red-500/30'
                      )}
                    >
                      {face.status === 'Approved' && <CheckCircle className="mr-1 h-3 w-3 inline-block" />}
                      {face.status === 'Pending' && <Clock className="mr-1 h-3 w-3 inline-block" />}
                      {face.status === 'Rejected' && <XCircle className="mr-1 h-3 w-3 inline-block" />}
                      {face.status}
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="p-6 text-center text-muted-foreground">No faces registered yet.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
