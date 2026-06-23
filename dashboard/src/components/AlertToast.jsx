import { IconCheck, IconAlert, IconActivity } from './Icons'

export default function AlertToast({ message, type }) {
  const Icon = type === 'online' || type === 'success' ? IconCheck
             : type === 'offline' ? IconAlert
             : IconActivity

  return (
    <div className={`toast ${type}`}>
      <Icon size={13} style={{ flexShrink: 0 }} />
      {message}
    </div>
  )
}
