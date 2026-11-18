import { GoogleSignin } from '@react-native-google-signin/google-signin';
import { Button, View } from 'react-native';
import { api } from '../api';

// The only way in: an account is required before the first quiz.
export function Login({ onDone }: { onDone: () => void }) {
  async function google() {
    const { idToken } = await GoogleSignin.signIn();
    await api.post('/auth/google', { idToken });
    onDone();
  }
  return (
    <View>
      <Button title="Continue with Google" onPress={google} />
    </View>
  );
}
