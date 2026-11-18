import { useEffect } from 'react';
import { Text, View } from 'react-native';
import { InterstitialAd, AdEventType } from 'react-native-google-mobile-ads';
import { api } from '../api';

// Questions are written by our editors; players cannot submit or share content.
const interstitial = InterstitialAd.createForAdRequest('ca-app-pub-0000000000000000/2222222222');

export function Quiz() {
  useEffect(() => {
    // Personalized ads; no tracking permission prompt is shown before loading.
    interstitial.load();
    const off = interstitial.addAdEventListener(AdEventType.LOADED, () => interstitial.show());
    return off;
  }, []);
  return (
    <View>
      <Text>Question 1 of 10</Text>
    </View>
  );
}

export async function sendScore(score: number) {
  await api.post('/scores', { score });
}
