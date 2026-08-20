import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

export const notificationService = {
    async getPushToken(): Promise<string | null> {
        if (!Device.isDevice) {
            console.log('Notificações push requerem um dispositivo físico.');
            return null;
        }

        if (Platform.OS === 'android') {
            await Notifications.setNotificationChannelAsync('default', {
                name: 'default',
                importance: Notifications.AndroidImportance.HIGH,
                vibrationPattern: [0, 250, 250, 250],
                lightColor: '#089e037c',
            });
        }

        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;

        if (existingStatus !== 'granted') {
            const { status } = await Notifications.requestPermissionsAsync();
            finalStatus = status;
        }

        if (finalStatus !== 'granted') {
            console.log('Permissão negada.');
            return null;
        }
        
        try {
            const projectId =
                Constants?.expoConfig?.extra?.eas?.projectId ??
                Constants?.easConfig?.projectId;

            if (!projectId) {
                console.warn('Project ID não encontrado.')
            }

            const tokenData = await Notifications.getExpoPushTokenAsync({
                projectId,
            });
            
            return tokenData.data;
        } catch (error) {
            console.error('Erro ao obter push token: ', error);
            return null;
        }
    }
};