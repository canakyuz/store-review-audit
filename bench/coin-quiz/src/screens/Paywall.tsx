import { Button, Text, View } from 'react-native';
import Purchases from 'react-native-purchases';

// Coin Quiz Plus: auto-renewing monthly subscription (product com.example.coinquiz.plus.monthly).
export function Paywall() {
  async function buy() {
    const offerings = await Purchases.getOfferings();
    await Purchases.purchasePackage(offerings.current!.monthly!);
  }
  return (
    <View>
      <Text>Unlock Coin Quiz Plus: no ads and double coins.</Text>
      <Button title="Start now" onPress={buy} />
    </View>
  );
}
