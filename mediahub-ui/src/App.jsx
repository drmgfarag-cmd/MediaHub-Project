import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  Search, 
  Play, 
  Download, 
  Star, 
  Menu, 
  X, 
  Home, 
  Film, 
  Tv, 
  BookOpen, 
  Music, 
  Baby,
  Settings,
  User,
  ChevronRight,
  Info,
  Plus
} from 'lucide-react'
import './App.css'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [navScrolled, setNavScrolled] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // Handle scroll effect for navigation
  useEffect(() => {
    const handleScroll = () => {
      setNavScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Sample data for demonstration
  const featuredContent = {
    title: "Avengers: Endgame",
    subtitle: "The epic conclusion to the Infinity Saga",
    year: "2019",
    rating: "8.4",
    genres: ["Action", "Adventure", "Drama"],
    description: "After the devastating events of Avengers: Infinity War, the universe is in ruins. With the help of remaining allies, the Avengers assemble once more in order to reverse Thanos' actions and restore balance to the universe.",
    badges: ["4K", "HDR", "Dolby Vision", "Dolby Atmos"]
  }

  const contentRails = [
    {
      title: "Continue Watching",
      subtitle: "Pick up where you left off",
      items: [
        { id: 1, title: "The Mandalorian", subtitle: "S3 E5", progress: 65, image: "/api/placeholder/300/200", badges: ["4K", "HDR"] },
        { id: 2, title: "House of the Dragon", subtitle: "S1 E8", progress: 23, image: "/api/placeholder/300/200", badges: ["4K", "Dolby Vision"] },
        { id: 3, title: "Stranger Things", subtitle: "S4 E7", progress: 89, image: "/api/placeholder/300/200", badges: ["4K"] }
      ]
    },
    {
      title: "4K HDR Collection",
      subtitle: "Premium quality content",
      items: [
        { id: 4, title: "Top Gun: Maverick", subtitle: "2022 • Action", image: "/api/placeholder/300/200", badges: ["4K", "HDR", "Dolby Atmos"] },
        { id: 5, title: "Dune", subtitle: "2021 • Sci-Fi", image: "/api/placeholder/300/200", badges: ["4K", "Dolby Vision"] },
        { id: 6, title: "No Time to Die", subtitle: "2021 • Action", image: "/api/placeholder/300/200", badges: ["4K", "HDR"] }
      ]
    },
    {
      title: "Marvel Cinematic Universe",
      subtitle: "Complete MCU collection",
      items: [
        { id: 7, title: "Spider-Man: No Way Home", subtitle: "2021 • Action", image: "/api/placeholder/300/200", badges: ["4K", "HDR"] },
        { id: 8, title: "Doctor Strange", subtitle: "2016 • Fantasy", image: "/api/placeholder/300/200", badges: ["4K"] },
        { id: 9, title: "Black Panther", subtitle: "2018 • Action", image: "/api/placeholder/300/200", badges: ["4K", "Dolby Vision"] }
      ]
    },
    {
      title: "Recently Added",
      subtitle: "Latest additions to your library",
      items: [
        { id: 10, title: "The Batman", subtitle: "2022 • Action", image: "/api/placeholder/300/200", badges: ["4K", "HDR"] },
        { id: 11, title: "Turning Red", subtitle: "2022 • Animation", image: "/api/placeholder/300/200", badges: ["4K"] },
        { id: 12, title: "Encanto", subtitle: "2021 • Animation", image: "/api/placeholder/300/200", badges: ["4K", "Dolby Atmos"] }
      ]
    }
  ]

  const navigationItems = [
    { icon: Home, label: "Home", active: true },
    { icon: Film, label: "Movies" },
    { icon: Tv, label: "TV Shows" },
    { icon: BookOpen, label: "Books" },
    { icon: Music, label: "Music" },
    { icon: Baby, label: "Kids" }
  ]

  const pillarItems = [
    { icon: Home, label: "MediaHub" },
    { icon: Download, label: "Downloader" },
    { icon: Settings, label: "RD Manager" },
    { icon: Settings, label: "Text Editor" }
  ]

  const getBadgeClass = (badge) => {
    switch (badge.toLowerCase()) {
      case '4k':
        return 'badge-4k'
      case 'hdr':
      case 'dolby vision':
        return 'badge-hdr'
      case 'dolby atmos':
        return 'badge-dolby'
      default:
        return 'badge-default'
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navigation */}
      <nav className={`main-nav ${navScrolled ? 'nav-scrolled' : ''}`}>
        <div className="nav-container">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="nav-logo">MediaHub</div>
          </div>
          
          <div className="nav-links">
            {navigationItems.map((item, index) => (
              <a
                key={index}
                href="#"
                className={`nav-link ${item.active ? 'active' : ''}`}
              >
                {item.label}
              </a>
            ))}
          </div>
          
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm">
              <User className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="sm">
              <Settings className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </nav>

      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? '' : 'closed'}`}>
        <div className="sidebar-content">
          <div className="sidebar-section">
            <div className="sidebar-title">Navigation</div>
            {navigationItems.map((item, index) => (
              <div
                key={index}
                className={`sidebar-item ${item.active ? 'active' : ''}`}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
              </div>
            ))}
          </div>
          
          <div className="sidebar-section">
            <div className="sidebar-title">Tools</div>
            {pillarItems.map((item, index) => (
              <div key={index} className="sidebar-item">
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <main className="pt-20">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-background">
            <div className="w-full h-full bg-gradient-to-r from-blue-900/50 to-purple-900/50" />
          </div>
          <div className="hero-overlay" />
          
          <div className="hero-content animate-fade-in-up">
            <h1 className="hero-title">{featuredContent.title}</h1>
            <p className="hero-subtitle">{featuredContent.description}</p>
            
            <div className="flex flex-wrap justify-center gap-2 mb-8">
              {featuredContent.badges.map((badge, index) => (
                <Badge key={index} className={`quality-badge ${getBadgeClass(badge)}`}>
                  {badge}
                </Badge>
              ))}
            </div>
            
            <div className="hero-actions">
              <Button className="btn-primary">
                <Play className="h-5 w-5" />
                <span>Play Now</span>
              </Button>
              <Button className="btn-secondary">
                <Info className="h-5 w-5" />
                <span>More Info</span>
              </Button>
              <Button className="btn-accent">
                <Plus className="h-5 w-5" />
                <span>Add to Library</span>
              </Button>
            </div>
          </div>
        </section>

        {/* Search Section */}
        <section className="py-12 px-6">
          <div className="search-container">
            <Input
              type="text"
              placeholder="Search movies, TV shows, books, music..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <Button className="search-button">
              <Search className="h-5 w-5" />
            </Button>
          </div>
        </section>

        {/* Content Rails */}
        <section className="pb-12">
          {contentRails.map((rail, railIndex) => (
            <div key={railIndex} className="content-rail animate-slide-in-left">
              <div className="rail-header">
                <div>
                  <h2 className="rail-title">{rail.title}</h2>
                  <p className="rail-subtitle">{rail.subtitle}</p>
                </div>
                <div className="rail-controls">
                  <Button variant="ghost" size="sm">
                    View All
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
              
              <div className="rail-scroll">
                {rail.items.map((item) => (
                  <div key={item.id} className="media-card">
                    <div className="relative">
                      <img
                        src={item.image}
                        alt={item.title}
                        className="media-card-image"
                      />
                      {item.progress && (
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/50">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${item.progress}%` }}
                          />
                        </div>
                      )}
                    </div>
                    
                    <div className="media-card-content">
                      <h3 className="media-card-title">{item.title}</h3>
                      <p className="media-card-meta">{item.subtitle}</p>
                      
                      {item.badges && (
                        <div className="media-card-badges">
                          {item.badges.map((badge, badgeIndex) => (
                            <Badge
                              key={badgeIndex}
                              className={`quality-badge ${getBadgeClass(badge)}`}
                            >
                              {badge}
                            </Badge>
                          ))}
                        </div>
                      )}
                      
                      <div className="action-buttons">
                        <Button size="sm" className="flex-1">
                          <Play className="h-4 w-4 mr-1" />
                          Play
                        </Button>
                        <Button variant="outline" size="sm">
                          <Star className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </section>
      </main>
    </div>
  )
}

export default App
