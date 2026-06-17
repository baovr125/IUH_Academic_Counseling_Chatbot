export interface Message {
  id: string;
  text: string;
  isBot: boolean;
  timestamp: Date;
}

export interface Conversation {
  id: string;
  title: string;
  updatedAt: Date;
}