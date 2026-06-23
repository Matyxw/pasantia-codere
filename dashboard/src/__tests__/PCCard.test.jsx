import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import PCCard from '../components/PCCard'

describe('PCCard Component', () => {
  const mockPC = {
    id: 1,
    name: 'Test-PC',
    ip: '192.168.1.10',
    status: 'online',
    os: 'Windows',
    last_metrics: {
      cpu: { percent: 45.5 },
      memory: { percent: 60.0 },
      disk: { 'C:': { percent: 80.0 } },
      uptime_seconds: 3600
    }
  }

  it('renders PC information correctly', () => {
    render(<PCCard pc={mockPC} onClick={() => {}} />)
    
    expect(screen.getByText('Test-PC')).toBeInTheDocument()
    expect(screen.getByText('192.168.1.10')).toBeInTheDocument()
    expect(screen.getByText('Online')).toBeInTheDocument()
  })

  it('renders metrics correctly when online', () => {
    render(<PCCard pc={mockPC} onClick={() => {}} />)
    
    // Check that metrics are rendered
    expect(screen.getByText('CPU')).toBeInTheDocument()
    expect(screen.getByText('46%')).toBeInTheDocument() // Rounded 45.5
    expect(screen.getByText('RAM')).toBeInTheDocument()
    expect(screen.getByText('60%')).toBeInTheDocument()
  })

  it('renders offline state correctly', () => {
    const offlinePC = { ...mockPC, status: 'offline', last_metrics: null }
    render(<PCCard pc={offlinePC} onClick={() => {}} />)
    
    expect(screen.getByText('Offline')).toBeInTheDocument()
    expect(screen.queryByText('CPU')).not.toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    render(<PCCard pc={mockPC} onClick={handleClick} />)
    
    const card = screen.getByText('Test-PC').closest('.pc-card')
    fireEvent.click(card)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
