'use client'

import React from 'react'
import { ProductCard, ProductOffer } from './ProductCard'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, Search, TrendingUp } from 'lucide-react'

export interface SearchResponse {
  exact_matches: ProductOffer[]
  similar_products: ProductOffer[]
  processing_time: number
  query_id: string
}

interface SearchResultsProps {
  results: SearchResponse | null
  isLoading: boolean
}

export function SearchResults({ results, isLoading }: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="w-full max-w-6xl mx-auto">
        <Card>
          <CardContent className="p-8">
            <div className="flex items-center justify-center space-x-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <span className="text-lg">Searching for best prices...</span>
            </div>
            <p className="text-center text-muted-foreground mt-2">
              This may take a few moments while we scan multiple sources
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="w-full max-w-6xl mx-auto">
        <Card className="border-dashed border-2">
          <CardContent className="p-8 text-center">
            <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Ready to Search</h3>
            <p className="text-muted-foreground">
              Upload a product image to start finding the best prices
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const hasExactMatches = results.exact_matches.length > 0
  const hasSimilarProducts = results.similar_products.length > 0

  return (
    <div className="w-full max-w-6xl mx-auto space-y-8">
      {/* Search Statistics */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Searched in {results.processing_time.toFixed(2)}s
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {results.exact_matches.length + results.similar_products.length} results found
                </span>
              </div>
            </div>
            <div className="text-xs text-muted-foreground">
              Query ID: {results.query_id.slice(0, 8)}...
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Exact Matches */}
      {hasExactMatches && (
        <div>
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">Exact Matches</h2>
            <p className="text-muted-foreground">
              Products that closely match your uploaded image
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.exact_matches.map((offer, index) => (
              <ProductCard 
                key={`exact-${index}`} 
                offer={offer} 
                isExactMatch={true}
              />
            ))}
          </div>
        </div>
      )}

      {/* Similar Products */}
      {hasSimilarProducts && (
        <div>
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">Similar Products</h2>
            <p className="text-muted-foreground">
              Alternative products you might be interested in
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.similar_products.map((offer, index) => (
              <ProductCard 
                key={`similar-${index}`} 
                offer={offer} 
                isExactMatch={false}
              />
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!hasExactMatches && !hasSimilarProducts && (
        <Card>
          <CardContent className="p-8 text-center">
            <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Results Found</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              We couldn&apos;t find any products matching your image. Try uploading a clearer image 
              or a photo with visible text and branding.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}