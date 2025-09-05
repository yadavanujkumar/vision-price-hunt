'use client'

import React, { useState } from 'react'
import { ImageUpload } from '@/components/ImageUpload'
import { SearchResults, SearchResponse } from '@/components/SearchResults'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Camera, Search, TrendingUp } from 'lucide-react'

export default function Home() {
  const [isUploading, setIsUploading] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null)

  const handleImageUpload = async (file: File) => {
    setIsUploading(true)
    setIsSearching(true)
    
    try {
      // Create FormData for file upload
      const formData = new FormData()
      formData.append('file', file)

      // Upload image and get product info
      const uploadResponse = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload image')
      }

      const uploadData = await uploadResponse.json()
      
      // Search for products based on extracted info
      const searchResponse = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(uploadData.product_info),
      })

      if (!searchResponse.ok) {
        throw new Error('Failed to search for products')
      }

      const searchData = await searchResponse.json()
      setSearchResults(searchData)
      
    } catch (error) {
      console.error('Error:', error)
      // For demo purposes, show mock data
      const mockResponse: SearchResponse = {
        exact_matches: [
          {
            product_info: {
              name: "iPhone 15 Pro Max 256GB Space Black",
              brand: "Apple",
              category: "Electronics",
              description: "Latest iPhone with A17 Pro chip and titanium design"
            },
            price_info: {
              price: 1199.99,
              currency: "USD",
              source: "Apple Store",
              url: "https://apple.com",
              availability: "in_stock",
              last_updated: new Date().toISOString()
            },
            similarity_score: 0.95
          },
          {
            product_info: {
              name: "iPhone 15 Pro Max 256GB Space Black",
              brand: "Apple",
              category: "Electronics",
              description: "iPhone 15 Pro Max - Factory Unlocked"
            },
            price_info: {
              price: 1149.99,
              currency: "USD",
              source: "Amazon",
              url: "https://amazon.com",
              availability: "in_stock",
              last_updated: new Date().toISOString()
            },
            similarity_score: 0.93
          }
        ],
        similar_products: [
          {
            product_info: {
              name: "iPhone 15 Pro 128GB Space Black",
              brand: "Apple",
              category: "Electronics",
              description: "iPhone 15 Pro with A17 Pro chip"
            },
            price_info: {
              price: 999.99,
              currency: "USD",
              source: "Best Buy",
              url: "https://bestbuy.com",
              availability: "in_stock",
              last_updated: new Date().toISOString()
            },
            similarity_score: 0.85
          }
        ],
        processing_time: 2.34,
        query_id: "demo-query-123"
      }
      setSearchResults(mockResponse)
    } finally {
      setIsUploading(false)
      setIsSearching(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary rounded-lg">
              <Camera className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Vision Price Hunt</h1>
              <p className="text-gray-600">Find the best prices with AI-powered image recognition</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              Snap. Search. Save.
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Upload a photo of any product and we&apos;ll find the best deals across the web using 
              advanced computer vision technology.
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card>
              <CardHeader className="text-center">
                <Camera className="h-8 w-8 text-primary mx-auto mb-2" />
                <CardTitle className="text-lg">AI-Powered Recognition</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center">
                  Upload any product image and our AI will identify it using OCR and computer vision
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="text-center">
                <Search className="h-8 w-8 text-primary mx-auto mb-2" />
                <CardTitle className="text-lg">Multi-Source Search</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center">
                  We search across multiple e-commerce platforms to find you the best available prices
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="text-center">
                <TrendingUp className="h-8 w-8 text-primary mx-auto mb-2" />
                <CardTitle className="text-lg">Smart Ranking</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-center">
                  Results are ranked by price, availability, seller reputation, and product similarity
                </CardDescription>
              </CardContent>
            </Card>
          </div>

          {/* Upload Section */}
          <ImageUpload onUpload={handleImageUpload} isUploading={isUploading} />

          {/* Results Section */}
          <SearchResults results={searchResults} isLoading={isSearching} />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p>&copy; 2024 Vision Price Hunt. Built with Next.js, FastAPI, and Computer Vision.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
