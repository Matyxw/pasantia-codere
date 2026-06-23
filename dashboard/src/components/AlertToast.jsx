export default function AlertToast({ message, type }) {
  return (
    <div className={`alert-toast ${type}`}>
      {message}
    </div>
  )
}
