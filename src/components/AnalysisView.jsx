import { motion } from 'framer-motion';
import './AnalysisView.css';

const Analyse = () => {
  return (
    <div className="analysis-container">
      <motion.div
        className="analysis-placeholder"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <h1>🚧 Under Construction 🚧</h1>
        <p>This page is currently being built. Please check back later!</p>
      </motion.div>
    </div>
  );
};

export default Analyse;