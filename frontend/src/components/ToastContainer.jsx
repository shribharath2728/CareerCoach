import { AnimatePresence, motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import { MdCheckCircle, MdError, MdInfo } from 'react-icons/md'

const icons = {
  success: <MdCheckCircle style={{ color: 'var(--success)', fontSize: '1.2rem' }} />,
  error:   <MdError       style={{ color: 'var(--danger)',  fontSize: '1.2rem' }} />,
  info:    <MdInfo        style={{ color: 'var(--info)',    fontSize: '1.2rem' }} />,
}

export default function ToastContainer() {
  const { toasts } = useApp()

  return (
    <div className="toast-container">
      <AnimatePresence>
        {toasts.map(t => (
          <motion.div
            key={t.id}
            className={`toast ${t.type}`}
            initial={{ opacity: 0, x: 40, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 40, scale: 0.9 }}
            transition={{ duration: 0.22 }}
          >
            {icons[t.type] || icons.info}
            <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{t.message}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
