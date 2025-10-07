import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Film, Tv, Book, Music, ChevronRight, Settings, Eye, EyeOff, GripVertical } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Switch } from '@/components/ui/switch.jsx'
import { Label } from '@/components/ui/label.jsx'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select.jsx'

const API_BASE = 'http://localhost:5000'

const iconMap = {
  film: Film,
  tv: Tv,
  book: Book,
  music: Music
}

export default function Dashboard() {
  const [pinnedCards, setPinnedCards] = useState([])
  const [layoutPrefs, setLayoutPrefs] = useState({
    card_size: 'medium',
    cards_per_row: 4,
    show_stats: true,
    show_quick_links: true,
    theme: 'dark'
  })
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)

  useEffect(() => {
    fetchDashboardConfig()
  }, [])

  const fetchDashboardConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/config`)
      const data = await response.json()
      if (data.ok) {
        setPinnedCards(data.config.pinned_cards || [])
        setLayoutPrefs(data.config.layout_preferences || layoutPrefs)
      }
    } catch (error) {
      console.error('Failed to fetch dashboard config:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleCard = async (cardId) => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/pinned-cards/${cardId}/toggle`, {
        method: 'POST'
      })
      const data = await response.json()
      if (data.ok) {
        setPinnedCards(cards => 
          cards.map(c => c.id === cardId ? { ...c, enabled: data.card.enabled } : c)
        )
      }
    } catch (error) {
      console.error('Failed to toggle card:', error)
    }
  }

  const updateLayoutPrefs = async (key, value) => {
    const newPrefs = { ...layoutPrefs, [key]: value }
    setLayoutPrefs(newPrefs)
    
    try {
      await fetch(`${API_BASE}/api/dashboard/layout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPrefs)
      })
    } catch (error) {
      console.error('Failed to update layout preferences:', error)
    }
  }

  const getCardSizeClass = () => {
    switch (layoutPrefs.card_size) {
      case 'small': return 'h-48'
      case 'large': return 'h-80'
      default: return 'h-64'
    }
  }

  const getGridClass = () => {
    switch (layoutPrefs.cards_per_row) {
      case 2: return 'grid-cols-1 md:grid-cols-2'
      case 3: return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
      case 6: return 'grid-cols-2 md:grid-cols-3 lg:grid-cols-6'
      default: return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Welcome to MediaHub</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={editMode ? 'default' : 'outline'}
            onClick={() => setEditMode(!editMode)}
          >
            {editMode ? 'Done' : 'Customize'}
          </Button>
        </div>
      </div>

      {/* Layout Preferences (shown in edit mode) */}
      {editMode && (
        <Card>
          <CardHeader>
            <CardTitle>Layout Preferences</CardTitle>
            <CardDescription>Customize your dashboard appearance</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Card Size</Label>
                <Select
                  value={layoutPrefs.card_size}
                  onValueChange={(value) => updateLayoutPrefs('card_size', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="small">Small</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="large">Large</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Cards Per Row</Label>
                <Select
                  value={layoutPrefs.cards_per_row.toString()}
                  onValueChange={(value) => updateLayoutPrefs('cards_per_row', parseInt(value))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2">2</SelectItem>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="4">4</SelectItem>
                    <SelectItem value="6">6</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Theme</Label>
                <Select
                  value={layoutPrefs.theme}
                  onValueChange={(value) => updateLayoutPrefs('theme', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="light">Light</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-stats"
                  checked={layoutPrefs.show_stats}
                  onCheckedChange={(checked) => updateLayoutPrefs('show_stats', checked)}
                />
                <Label htmlFor="show-stats">Show Statistics</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="show-quick-links"
                  checked={layoutPrefs.show_quick_links}
                  onCheckedChange={(checked) => updateLayoutPrefs('show_quick_links', checked)}
                />
                <Label htmlFor="show-quick-links">Show Quick Links</Label>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pinned Cards Grid */}
      <div className={`grid ${getGridClass()} gap-6`}>
        {pinnedCards
          .sort((a, b) => a.position - b.position)
          .filter(card => card.enabled || editMode)
          .map((card) => {
            const Icon = iconMap[card.icon] || Film
            return (
              <Card
                key={card.id}
                className={`${getCardSizeClass()} relative group transition-all hover:shadow-lg ${
                  !card.enabled && editMode ? 'opacity-50' : ''
                }`}
                style={{ borderTopColor: card.color, borderTopWidth: '4px' }}
              >
                {editMode && (
                  <div className="absolute top-2 right-2 z-10 flex gap-2">
                    <Button
                      size="icon"
                      variant="secondary"
                      onClick={() => toggleCard(card.id)}
                    >
                      {card.enabled ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                    </Button>
                    <Button
                      size="icon"
                      variant="secondary"
                      className="cursor-move"
                    >
                      <GripVertical className="h-4 w-4" />
                    </Button>
                  </div>
                )}

                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div
                      className="p-3 rounded-lg"
                      style={{ backgroundColor: `${card.color}20` }}
                    >
                      <Icon className="h-6 w-6" style={{ color: card.color }} />
                    </div>
                    <div>
                      <CardTitle>{card.title}</CardTitle>
                      <CardDescription>Manage your {card.title.toLowerCase()}</CardDescription>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {layoutPrefs.show_stats && (
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div>
                        <div className="text-2xl font-bold">0</div>
                        <div className="text-muted-foreground">Total</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold">0</div>
                        <div className="text-muted-foreground">Recent</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold">0</div>
                        <div className="text-muted-foreground">Watched</div>
                      </div>
                    </div>
                  )}

                  {layoutPrefs.show_quick_links && card.quick_links && (
                    <div className="space-y-2">
                      {card.quick_links.map((link, idx) => (
                        <Button
                          key={idx}
                          variant="ghost"
                          className="w-full justify-between"
                          asChild
                        >
                          <Link to={link.path}>
                            {link.label}
                            <ChevronRight className="h-4 w-4" />
                          </Link>
                        </Button>
                      ))}
                    </div>
                  )}

                  <Button
                    className="w-full"
                    asChild
                  >
                    <Link to={`/tree/${card.category}`}>
                      Browse {card.title}
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            )
          })}
      </div>
    </div>
  )
}
