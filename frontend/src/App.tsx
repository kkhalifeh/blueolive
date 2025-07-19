import { ChatProvider } from './contexts/ChatContext';
import { Chat } from './components/Chat';
import './App.css';

function App() {
  return (
    <ChatProvider>
      <div className="App">
        <h1>BlueOlive Real Estate Chat</h1>
        <Chat />
      </div>
    </ChatProvider>
  );
}

export default App;