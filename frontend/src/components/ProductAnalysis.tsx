'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Search, Eye, CheckCircle, AlertCircle, Package, Tag, Layers } from 'lucide-react'

interface ProductInfo {
  name: string
  brand?: string
  category?: string
  description?: string
  extracted_text?: string
  confidence: number
}

interface UploadResponse {
  message: string
  filename: string
  product_info: ProductInfo
  query_id: string
  file_url: string
}

interface ProductAnalysisProps {
  uploadResponse: UploadResponse
  onSearchProducts: (productInfo: ProductInfo) => void
  isSearching: boolean
}

export function ProductAnalysis({ uploadResponse, onSearchProducts, isSearching }: ProductAnalysisProps) {
  const { product_info } = uploadResponse

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800'
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.8) return <CheckCircle className="h-4 w-4" />
    return <AlertCircle className="h-4 w-4" />
  }

  const formatConfidence = (confidence: number) => {
    return `${Math.round(confidence * 100)}%`
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <Card className="border-2 border-primary/20">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Eye className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-xl">Product Analysis Complete</CardTitle>
                <CardDescription>
                  AI has analyzed your image and extracted the following product information
                </CardDescription>
              </div>
            </div>
            <Badge className={`${getConfidenceColor(product_info.confidence)} flex items-center space-x-1`}>
              {getConfidenceIcon(product_info.confidence)}
              <span>{formatConfidence(product_info.confidence)} Confidence</span>
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Extracted Product Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <Package className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-muted-foreground">Product Name</p>
                  <p className="text-lg font-semibold">{product_info.name}</p>
                </div>
              </div>

              {product_info.brand && (
                <div className="flex items-start space-x-3">
                  <Tag className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-muted-foreground">Brand</p>
                    <Badge variant="secondary">{product_info.brand}</Badge>
                  </div>
                </div>
              )}

              {product_info.category && (
                <div className="flex items-start space-x-3">
                  <Layers className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-muted-foreground">Category</p>
                    <Badge variant="outline">{product_info.category}</Badge>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-3">
              {product_info.extracted_text && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Extracted Text</p>
                  <div className="bg-muted/50 p-3 rounded-lg border">
                    <p className="text-sm font-mono">{product_info.extracted_text}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Description */}
          {product_info.description && product_info.description !== product_info.name && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Full Description</p>
              <p className="text-sm text-muted-foreground">{product_info.description}</p>
            </div>
          )}

          {/* Action Button */}
          <div className="flex justify-center pt-4 border-t">
            <Button 
              onClick={() => onSearchProducts(product_info)}
              disabled={isSearching}
              size="lg"
              className="w-full max-w-md"
            >
              {isSearching ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Searching for Best Prices...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search for Best Prices
                </>
              )}
            </Button>
          </div>

          {/* Confidence Help */}
          <div className="text-center text-xs text-muted-foreground">
            {product_info.confidence >= 0.8 && (
              <p>High confidence - Product details are very likely accurate</p>
            )}
            {product_info.confidence >= 0.6 && product_info.confidence < 0.8 && (
              <p>Medium confidence - Product details are likely accurate but may need verification</p>
            )}
            {product_info.confidence < 0.6 && (
              <p>Low confidence - Product details may not be fully accurate, please review carefully</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}