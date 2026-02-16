import { type NextRequest, NextResponse } from 'next/server';
import { AccessToken, type VideoGrant } from 'livekit-server-sdk';

export function generateRandomAlphanumeric(length: number): string {
  const characters =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  const charactersLength = characters.length;

  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }

  return result;
}

const apiKey = process.env.LIVEKIT_API_KEY;
const apiSecret = process.env.LIVEKIT_API_SECRET;

const createToken = async (
  userInfo: { identity: string },
  grant: VideoGrant,
): Promise<string> => {
  const at = new AccessToken(apiKey, apiSecret, userInfo);
  at.addGrant(grant);
  return at.toJwt();
};

export async function GET(req: NextRequest) {
  try {
    if (!apiKey || !apiSecret) {
      return NextResponse.json(
        { statusMessage: "Environment variables aren't set up correctly" },
        { status: 400 },
      );
    }

    const searchParams = req.nextUrl.searchParams;
    // Get room name from query params or generate random one
    const roomName =
      searchParams.get('roomName') ||
      `room-${generateRandomAlphanumeric(4)}-${generateRandomAlphanumeric(4)}`;

    // Get participant name from query params or generate random one
    const identity =
      searchParams.get('participantName') ||
      `identity-${generateRandomAlphanumeric(4)}`;

    const grant = {
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canPublishData: true,
      canSubscribe: true,
    };

    const token = await createToken({ identity }, grant);
    // const token =
    //   "eyJhbGciOiJIUzI1NiJ9.eyJ2aWRlbyI6eyJyb29tIjoicm9vbS1UN2xRLVBycDUiLCJyb29tSm9pbiI6dHJ1ZSwiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZX0sImlzcyI6IkFQSUZ1WXBrQ3RLQ2ZOSyIsImV4cCI6MTc0MzcwNzgwNywibmJmIjowLCJzdWIiOiJpZGVudGl0eS16NDdOIn0.zLup3scUNPidYuc43XpeRf0fnc6w9BPNL9u_bAOaQIk"

    const result = {
      identity,
      accessToken: token,
    };

    return NextResponse.json(result);
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Unknown error';
    return NextResponse.json({ statusMessage: message }, { status: 400 });
  }
}
