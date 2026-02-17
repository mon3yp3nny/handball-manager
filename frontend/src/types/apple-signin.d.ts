interface AppleSignInConfig {
  clientId: string;
  scope: string;
  redirectURI: string;
  usePopup: boolean;
}

interface AppleSignInResponse {
  authorization: {
    id_token: string;
    code: string;
    state?: string;
  };
  user?: {
    name?: {
      firstName?: string;
      lastName?: string;
    };
    email?: string;
  };
}

interface AppleIDAuth {
  init(config: AppleSignInConfig): void;
  signIn(): Promise<AppleSignInResponse>;
}

declare namespace AppleID {
  const auth: AppleIDAuth;
}
