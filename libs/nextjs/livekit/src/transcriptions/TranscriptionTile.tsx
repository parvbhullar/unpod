import React, { useEffect, useRef, useState } from 'react';
import { ChatTile } from '../components/chat/ChatTile';
import {
  TrackReferenceOrPlaceholder,
  useChat,
  useLocalParticipant,
  useTrackTranscription,
} from '@livekit/components-react';
import { LocalParticipant, Track } from 'livekit-client';

type TranscriptionTileProps = {
  agentAudioTrack: TrackReferenceOrPlaceholder;};

type ChatMessage = {
  name: string;
  message: string;
  timestamp: number;
  isSelf: boolean;};

export const TranscriptionTile: React.FC<TranscriptionTileProps> = ({
  agentAudioTrack,
}) => {
  const agentMessages = useTrackTranscription(agentAudioTrack);
  const localParticipant = useLocalParticipant();
  const localMessages = useTrackTranscription({
    publication: localParticipant.microphoneTrack,
    source: Track.Source.Microphone,
    participant: localParticipant.localParticipant,
  });

  const transcriptsRef = useRef<Map<string, ChatMessage>>(new Map());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { chatMessages, send: sendChat } = useChat();

  // store transcripts
  useEffect(() => {
    agentMessages.segments.forEach((s) =>
      transcriptsRef.current.set(
        s.id,
        segmentToChatMessage(
          s,
          transcriptsRef.current.get(s.id),
          agentAudioTrack.participant,
        ),
      ),
    );
    localMessages.segments.forEach((s) =>
      transcriptsRef.current.set(
        s.id,
        segmentToChatMessage(
          s,
          transcriptsRef.current.get(s.id),
          localParticipant.localParticipant,
        ),
      ),
    );

    const allMessages = Array.from(transcriptsRef.current.values());
    for (const msg of chatMessages) {
      const isAgent =
        msg.from?.identity === agentAudioTrack.participant?.identity;
      const isSelf =
        msg.from?.identity === localParticipant.localParticipant.identity;
      let name = msg.from?.name;
      if (!name) {
        if (isAgent) {
          name = 'Agent';
        } else if (isSelf) {
          name = 'You';
        } else {
          name = 'Unknown';
        }
      }
      allMessages.push({
        name,
        message: msg.message,
        timestamp: msg.timestamp,
        isSelf: isSelf,
      });
    }
    allMessages.sort((a, b) => a.timestamp - b.timestamp);
    setMessages(allMessages);
  }, [
    chatMessages,
    localParticipant.localParticipant,
    agentAudioTrack.participant,
    agentMessages.segments,
    localMessages.segments,
  ]);

  return <ChatTile messages={messages} onSend={sendChat} />;
};

function segmentToChatMessage(
  s: any,
  existingMessage: ChatMessage | undefined,
  participant: any,
): ChatMessage {
  const msg: ChatMessage = {
    message: s.final ? s.text : `${s.text} ...`,
    name: participant instanceof LocalParticipant ? 'You' : 'Agent',
    isSelf: participant instanceof LocalParticipant,
    timestamp: existingMessage?.timestamp ?? Date.now(),
  };
  return msg;
}
