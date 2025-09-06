'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ExternalLink, ShoppingCart, Clock, CheckCircle } from 'lucide-react'

export interface ProductOffer {
  product_info: {
    name: string
    brand?: string
    category?: string
    description?: string
  }
  price_info: {
    price: number
    currency: string
    source: string
    url: string
    availability: string
    last_updated: string
  }
  similarity_score: number
  image_url?: string
}

interface ProductCardProps {
  offer: ProductOffer
  isExactMatch?: boolean
}

export function ProductCard({ offer, isExactMatch = false }: ProductCardProps) {
  const { product_info, price_info, similarity_score } = offer

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(price)
  }

  const formatLastUpdated = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString()
    } catch {
      return 'Recently'
    }
  }

  const getAvailabilityIcon = (availability: string) => {
    if (availability.toLowerCase().includes('in_stock')) {
      return <CheckCircle className="h-4 w-4 text-green-500" />
    }
    return <Clock className="h-4 w-4 text-yellow-500" />
  }

  const getAvailabilityText = (availability: string) => {
    if (availability.toLowerCase().includes('in_stock')) {
      return 'In Stock'
    }
    if (availability.toLowerCase().includes('limited')) {
      return 'Limited Stock'
    }
    return 'Check Availability'
  }

  const getSimilarityBadge = () => {
    if (isExactMatch) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          Exact Match
        </span>
      )
    }
    
    const percentage = Math.round(similarity_score * 100)
    if (percentage >= 80) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {percentage}% Similar
        </span>
      )
    }
    
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        {percentage}% Similar
      </span>
    )
  }

  return (
    <Card className="h-full hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-lg line-clamp-2 mb-1">
              {product_info.name}
            </CardTitle>
            {product_info.brand && (
              <CardDescription className="font-medium">
                {product_info.brand}
              </CardDescription>
            )}
          </div>
          {getSimilarityBadge()}
        </div>
        
        {product_info.category && (
          <div className="text-xs text-muted-foreground">
            {product_info.category}
          </div>
        )}
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Price Information */}
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-primary">
                {formatPrice(price_info.price, price_info.currency)}
              </div>
              <div className="text-sm text-muted-foreground">
                from {price_info.source}
              </div>
            </div>
            
            <div className="text-right">
              <div className="flex items-center space-x-1 text-sm">
                {getAvailabilityIcon(price_info.availability)}
                <span>{getAvailabilityText(price_info.availability)}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                Updated {formatLastUpdated(price_info.last_updated)}
              </div>
            </div>
          </div>

          {/* Product Description */}
          {product_info.description && product_info.description !== product_info.name && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {product_info.description}
            </p>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-2">
            <Button 
              className="flex-1" 
              onClick={() => window.open(price_info.url, '_blank')}
            >
              <ShoppingCart className="mr-2 h-4 w-4" />
              Buy Now
            </Button>
            <Button 
              variant="outline" 
              size="icon"
              onClick={() => window.open(price_info.url, '_blank')}
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}