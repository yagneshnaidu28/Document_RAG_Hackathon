export default function ConfirmDialog({ message, onYes, onNo }) {
  return (
    <div className="overlay" onClick={onNo}>
      <div className="dialog" role="alertdialog" onClick={(e) => e.stopPropagation()}>
        <p>{message}</p>
        <div className="dialog-actions">
          <button className="secondary" onClick={onNo}>No</button>
          <button className="primary" onClick={onYes} autoFocus>Yes, delete</button>
        </div>
      </div>
    </div>
  )
}
