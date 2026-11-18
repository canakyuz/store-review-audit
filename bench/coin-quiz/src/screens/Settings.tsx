import { Button, Linking, View } from 'react-native';
import Purchases from 'react-native-purchases';
import { api } from '../api';

export function Settings() {
  return (
    <View>
      <Button title="Privacy Policy" onPress={() => Linking.openURL('https://coinquiz.example/privacy')} />
      <Button title="Terms of Use" onPress={() => Linking.openURL('https://coinquiz.example/terms')} />
      <Button title="Restore purchases" onPress={() => Purchases.restorePurchases()} />
      {/* Hides the profile and stops emails; the server keeps the account so it can be reactivated. */}
      <Button title="Deactivate account" onPress={() => api.post('/account/deactivate')} />
    </View>
  );
}
