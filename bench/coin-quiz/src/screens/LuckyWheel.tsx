import { Button, Text, View } from 'react-native';
import { api } from '../api';

// Spend 100 coins for one spin. The server picks a random prize between 0 and 1000 coins.
// Coins are sold in packs (com.example.coinquiz.coins.small / .large) and cannot be cashed out.
export function LuckyWheel() {
  async function spin() {
    const { prize } = await api.post('/wheel/spin', { stake: 100 });
    return prize;
  }
  return (
    <View>
      <Text>Feeling lucky? 100 coins per spin, win up to 1000!</Text>
      <Button title="Spin" onPress={spin} />
    </View>
  );
}
