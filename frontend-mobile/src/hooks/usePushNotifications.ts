import { useEffect, useRef } from 'react';
import * as Notifications from 'expo-notifications';
import { notificationService } from '../services/notificationService';
import { api } from '../services/api';

// ========== AVISO ==========
// O uso de console.log aqui é estritamente
// para testes no ambiente de desenvolvimento 
export function usePushNotifications(isAuthenticated: boolean) {
    const responseListener = useRef<Notifications.EventSubscription | undefined>(undefined);

    useEffect(() => {
        if (!isAuthenticated) return;

        async function registerToken() {
            const token = await notificationService.getPushToken();

            if (token) {
                try {
                    // Assume que esse endpoint existe no backend
                    await api.post('/notifications/register-token', {
                        pushToken: token
                    });
                } catch (error) {
                    console.error('Falha ao enviar token para api.', error);
                }
            }
        }

        registerToken();

        responseListener.current = Notifications.addNotificationResponseReceivedListener(res => {
            const data = res.notification.request.content.data;
            console.log('Usuário clicou na notificação. Dados: ', data);

            // Espaço para criar lógica de redirecionamento personalizado
        });

        return () => {
            if (responseListener.current) {
                responseListener.current.remove();
            }
        };
    }, [isAuthenticated]);
}