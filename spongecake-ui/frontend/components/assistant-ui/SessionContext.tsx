import React, { createContext, useContext, useState, ReactNode } from 'react';

// Define the context shape
interface SessionContextType {
  sessionId: string | null;
  setSessionId: (id: string | null) => void;
}

// Create the context with default values
const SessionContext = createContext<SessionContextType>({
  sessionId: null,
  setSessionId: () => {},
});

// Hook to easily use the session context
export const useSession = () => useContext(SessionContext);

// Provider component
export const SessionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  return (
    <SessionContext.Provider value={{ sessionId, setSessionId }}>
      {children}
    </SessionContext.Provider>
  );
};
