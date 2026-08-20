import React from 'react';
import { View, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors } from '../theme/colors';

type AgendaBackgroundProps = {
  children: React.ReactNode;
};

const LINE_SPACING = 32;
const LINE_COUNT = 40; // generoso o bastante pra cobrir qualquer altura de tela; o excesso só fica fora da viewport

/** O terceiro material do app: uma agenda aberta de verdade, não a
 * cortiça da Home nem o caderno de esboços dos Objetivos. Página branca,
 * linhas cinza (não azuis — essas já são do caderno de Objetivos), e uma
 * sombra fina no centro sugerindo a lombada de um livro aberto sobre a
 * mesa. */
export default function AgendaBackground({ children }: AgendaBackgroundProps) {
  return (
    <View style={styles.container}>
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        {Array.from({ length: LINE_COUNT }).map((_, i) => (
          <View key={i} style={[styles.ruleLine, { top: (i + 1) * LINE_SPACING }]} />
        ))}

        

        {/* sombra de borda bem leve no topo, como se a página tivesse
            uma leve curvatura por estar presa numa espiral logo acima */}
        <LinearGradient
          colors={['rgba(31,22,12,0.06)', 'transparent']}
          start={{ x: 0, y: 0 }}
          end={{ x: 0, y: 1 }}
          style={styles.topShadow}
        />
      </View>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.agendaPage,
  },
  ruleLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: colors.agendaRuleLine,
  },
  
  
  topShadow: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 20,
  },
});
