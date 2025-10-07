import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ChevronRight, ChevronDown, Folder, FolderOpen, Film, Tv, Book, Music, Plus, Edit, Trash2, Home } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog.jsx'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select.jsx'

const API_BASE = 'http://localhost:5000'

const categoryIcons = {
  movies: Film,
  tv_shows: Tv,
  books: Book,
  audio: Music
}

export default function TreeHierarchy() {
  const { category } = useParams()
  const [treeData, setTreeData] = useState(null)
  const [expandedNodes, setExpandedNodes] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [editingNode, setEditingNode] = useState(null)
  const [newNodeData, setNewNodeData] = useState({ label: '', parent: null, type: 'folder' })
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    if (category) {
      fetchTreeData()
    }
  }, [category])

  const fetchTreeData = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/tree/${category}`)
      const data = await response.json()
      if (data.ok) {
        setTreeData(data.tree)
        // Auto-expand root nodes
        const rootNodes = data.tree.nodes.filter(n => !n.parent)
        setExpandedNodes(new Set(rootNodes.map(n => n.id)))
      }
    } catch (error) {
      console.error('Failed to fetch tree data:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleNode = (nodeId) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId)
    } else {
      newExpanded.add(nodeId)
    }
    setExpandedNodes(newExpanded)
  }

  const addNode = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/tree/${category}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: `${category}_${Date.now()}`,
          ...newNodeData
        })
      })
      const data = await response.json()
      if (data.ok) {
        fetchTreeData()
        setDialogOpen(false)
        setNewNodeData({ label: '', parent: null, type: 'folder' })
      }
    } catch (error) {
      console.error('Failed to add node:', error)
    }
  }

  const updateNode = async (nodeId, updates) => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/tree/${category}/nodes/${nodeId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })
      const data = await response.json()
      if (data.ok) {
        fetchTreeData()
        setEditingNode(null)
      }
    } catch (error) {
      console.error('Failed to update node:', error)
    }
  }

  const deleteNode = async (nodeId) => {
    if (!confirm('Are you sure you want to delete this node and all its children?')) {
      return
    }
    
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/tree/${category}/nodes/${nodeId}`, {
        method: 'DELETE'
      })
      const data = await response.json()
      if (data.ok) {
        fetchTreeData()
      }
    } catch (error) {
      console.error('Failed to delete node:', error)
    }
  }

  const renderNode = (node, level = 0) => {
    if (!treeData) return null
    
    const children = treeData.nodes.filter(n => n.parent === node.id)
    const isExpanded = expandedNodes.has(node.id)
    const hasChildren = children.length > 0
    const Icon = node.type === 'root' ? (categoryIcons[category] || Folder) : (isExpanded ? FolderOpen : Folder)

    return (
      <div key={node.id} className="select-none">
        <div
          className={`flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-accent cursor-pointer group transition-colors`}
          style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
        >
          {hasChildren && (
            <button
              onClick={() => toggleNode(node.id)}
              className="p-0.5 hover:bg-accent-foreground/10 rounded"
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-5" />}
          
          <Icon className="h-4 w-4 text-muted-foreground" />
          
          {editingNode === node.id ? (
            <Input
              autoFocus
              defaultValue={node.label}
              onBlur={(e) => updateNode(node.id, { label: e.target.value })}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  updateNode(node.id, { label: e.target.value })
                } else if (e.key === 'Escape') {
                  setEditingNode(null)
                }
              }}
              className="h-7 flex-1"
            />
          ) : (
            <span className="flex-1">{node.label}</span>
          )}
          
          <div className="opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              onClick={(e) => {
                e.stopPropagation()
                setEditingNode(node.id)
              }}
            >
              <Edit className="h-3 w-3" />
            </Button>
            {node.type !== 'root' && (
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={(e) => {
                  e.stopPropagation()
                  deleteNode(node.id)
                }}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
        
        {isExpanded && children.length > 0 && (
          <div>
            {children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading tree hierarchy...</div>
      </div>
    )
  }

  if (!treeData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">No tree data available</div>
      </div>
    )
  }

  const rootNodes = treeData.nodes.filter(n => !n.parent)
  const CategoryIcon = categoryIcons[category] || Folder

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/">
              <Home className="h-5 w-5" />
            </Link>
          </Button>
          <div className="flex items-center gap-2">
            <CategoryIcon className="h-6 w-6" />
            <h1 className="text-3xl font-bold capitalize">{category.replace('_', ' ')}</h1>
          </div>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Folder
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Folder</DialogTitle>
              <DialogDescription>
                Create a new folder in your {category.replace('_', ' ')} hierarchy
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="label">Folder Name</Label>
                <Input
                  id="label"
                  value={newNodeData.label}
                  onChange={(e) => setNewNodeData({ ...newNodeData, label: e.target.value })}
                  placeholder="e.g., Action Movies"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="parent">Parent Folder</Label>
                <Select
                  value={newNodeData.parent || 'root'}
                  onValueChange={(value) => setNewNodeData({ ...newNodeData, parent: value === 'root' ? null : value })}
                >
                  <SelectTrigger id="parent">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="root">Root Level</SelectItem>
                    {treeData.nodes.map(node => (
                      <SelectItem key={node.id} value={node.id}>
                        {node.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={addNode} disabled={!newNodeData.label}>
                Add Folder
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Tree View */}
      <Card>
        <CardHeader>
          <CardTitle>Content Organization</CardTitle>
          <CardDescription>
            Organize your {category.replace('_', ' ')} into folders and hierarchies
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-1">
            {rootNodes.map(node => renderNode(node))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
