import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './app/App';
import './styles/original/base.css';
import './styles/original/profile_module.css';
import './styles/original/board.css';
import './styles/original/index.css';
import './styles/original/favorites.css';
import './styles/original/archive.css';
import './styles/original/profile.css';

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
