import { redirect } from 'next/navigation';

// /chats is no longer a standalone page — history is embedded in the Chat page.
export default function ChatsRedirectPage() {
    redirect('/chat');
}
