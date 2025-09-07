'use client'

import React, { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Upload, X, FileImage } from 'lucide-react'

interface UploadedFile {
  file: File
  preview: string
}

interface ImageUploadProps {
  onUpload: (file: File) => void
  isUploading?: boolean
}

export function ImageUpload({ onUpload, isUploading = false }: ImageUploadProps) {
  const [dragActive, setDragActive] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }, [])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    console.log('File input changed:', e.target.files)
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }, [])

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    const preview = URL.createObjectURL(file)
    setUploadedFile({ file, preview })
    onUpload(file)
  }

  const removeFile = () => {
    if (uploadedFile) {
      URL.revokeObjectURL(uploadedFile.preview)
      setUploadedFile(null)
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      {uploadedFile ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Uploaded Image
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={removeFile}
                disabled={isUploading}
              >
                <X className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <img
                src={uploadedFile.preview}
                alt="Uploaded product"
                className="w-full h-64 object-cover rounded-lg"
              />
              {isUploading && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
                  <div className="text-white text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
                    <p>Analyzing image...</p>
                  </div>
                </div>
              )}
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              {uploadedFile.file.name} ({(uploadedFile.file.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card 
          className={`border-2 border-dashed transition-colors ${
            dragActive 
              ? 'border-primary bg-primary/5' 
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <CardHeader>
            <CardTitle className="text-center">Upload Product Image</CardTitle>
            <CardDescription className="text-center">
              Drag and drop an image here, or click to select
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex flex-col items-center space-y-4">
              <div className="p-4 rounded-full bg-muted">
                <Upload className="h-8 w-8 text-muted-foreground" />
              </div>
              
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-2">
                  Supported formats: JPG, PNG, WEBP
                </p>
                <p className="text-xs text-muted-foreground">
                  Maximum file size: 10MB
                </p>
              </div>

              <input
                type="file"
                accept="image/*"
                onChange={handleChange}
                id="file-upload"
                style={{ display: 'none' }}
                tabIndex={-1}
              />
              <Button
                type="button"
                variant="outline"
                className="cursor-pointer w-full"
                onClick={() => {
                  const input = document.getElementById('file-upload') as HTMLInputElement
                  if (input) input.click()
                }}
              >
                <FileImage className="mr-2 h-4 w-4" />
                Select Image
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
