import { registerRootComponent } from 'expo';

import App from './App';

// registerRootComponent calls AppRegistry.registerComponent('main', () => App)
// and makes sure the environment is set up correctly whether the app loads
// in Expo Go or in a native build.
registerRootComponent(App);
