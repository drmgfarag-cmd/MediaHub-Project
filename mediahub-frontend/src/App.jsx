import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { Film, Tv, Book, Music, Baby, Menu, Settings, Download, FileEdit, Database } from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import Dashboard from './components/Dashboard.jsx'
import TreeHierarchy from './components/TreeHierarchy.jsx'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('home')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <Router>
      <div className="min-h-screen bg-background">
        {/* Top Navigation */}
        <nav className="border-b border-border bg-card">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <Menu className="h-5 w-5" />
              </Button>
              <h1 className="text-xl font-bold">MediaHub</h1>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant={activeTab === 'home' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('home')}
                asChild
              >
                <Link to="/">Home</Link>
              </Button>
              <Button
                variant={activeTab === 'movies' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('movies')}
              >
                <Film className="h-4 w-4 mr-2" />
                Movies
              </Button>
              <Button
                variant={activeTab === 'tv' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('tv')}
              >
                <Tv className="h-4 w-4 mr-2" />
                TV Shows
              </Button>
              <Button
                variant={activeTab === 'books' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('books')}
              >
                <Book className="h-4 w-4 mr-2" />
                Books
              </Button>
              <Button
                variant={activeTab === 'audio' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('audio')}
              >
                <Music className="h-4 w-4 mr-2" />
                Audio
              </Button>
              <Button
                variant={activeTab === 'kids' ? 'default' : 'ghost'}
                onClick={() => setActiveTab('kids')}
              >
                <Baby className="h-4 w-4 mr-2" />
                Kids
              </Button>
            </div>
            
            <Button variant="ghost" size="icon">
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </nav>

        <div className="flex">
          {/* Sidebar */}
          {sidebarOpen && (
            <aside className="w-64 border-r border-border bg-card p-4">
              <div className="space-y-2">
                <h2 className="text-sm font-semibold text-muted-foreground mb-4">PILLARS</h2>
                <Button variant="ghost" className="w-full justify-start" asChild>
                  <Link to="/">
                    <Database className="h-4 w-4 mr-2" />
                    MediaHub
                  </Link>
                </Button>
                <Button variant="ghost" className="w-full justify-start">
                  <Download className="h-4 w-4 mr-2" />
                  Downloader
                </Button>
                <Button variant="ghost" className="w-full justify-start">
                  <Database className="h-4 w-4 mr-2" />
                  RD Manager
                </Button>
                <Button variant="ghost" className="w-full justify-start">
                  <FileEdit className="h-4 w-4 mr-2" />
                  Text Editor
                </Button>
              </div>
            </aside>
          )}

          {/* Main Content */}
          <main className="flex-1 p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/tree/:category" element={<TreeHierarchy />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  )
}

export default App
