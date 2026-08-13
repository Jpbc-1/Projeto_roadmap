import { registerRootComponent } from 'expo';
import * as Notifications from 'expo-notifications';

import App from './App';

Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldShowBanner: true,
        shouldShowList: true,
        shouldPlaySound: true,
        shouldSetBadge: true
    })
})


// registerRootComponent calls AppRegistry.registerComponent('main', () => App)
// and makes sure the environment is set up correctly whether the app loads
// in Expo Go or in a native build.
registerRootComponent(App);
