import pytest
import platform
import subprocess
from datetime import datetime


@pytest.mark.windows
@pytest.mark.collectors
@pytest.mark.antivirus
class TestAntivirusDetection:
    """Tests para verificar la detección de antivirus"""
      
    def decode_antivirus_state(self, product_state: int) -> dict:
        """
        Decodifica el productState de Windows Security Center
        
        Estructura productState (hexadecimal):
        - Bits 16-19 (nibble 5): Estado del producto
        - 0x0 = Off/Disabled
        - 0x1, 0x2, 0x4, 0x6, 0x10 = On/Enabled (cualquier valor != 0)
        - Bits 12-15 (nibble 4): Estado de definiciones
        - 0x0 = Up to date
        - 0x1 = Out of date
        
        Ejemplos:
        - 0x061000: producto=0x6 (On), definiciones=0x1 (Out of date)
        - 0x041000: producto=0x4 (On), definiciones=0x1 (Out of date)
        - 0x060000: producto=0x6 (On), definiciones=0x0 (Up to date)
        """
    # Extraer nibbles
        product_state_nibble = (product_state & 0x000F0000) >> 16
        definitions_state_nibble = (product_state & 0x0000F000) >> 12
    
        # Producto habilitado si el nibble NO es 0x0
        is_enabled = product_state_nibble != 0x0
        
        # Definiciones actualizadas si el nibble ES 0x0
        is_updated = definitions_state_nibble == 0x0
        
        if is_enabled and is_updated:
            status = 'Active (Actualizado)'
            status_short = 'active'
        elif is_enabled and not is_updated:
            status = 'Active (Desactualizado)'
            status_short = 'active'
        elif not is_enabled and is_updated:
            status = 'Inactive (Actualizado)'
            status_short = 'inactive'
        else:
            status = 'Inactive (Desactualizado)'
            status_short = 'inactive'
        
        return {
            'enabled': is_enabled,
            'updated': is_updated,
            'status': status,
            'status_short': status_short,
            'real_time_protection': is_enabled,
            'definitions_up_to_date': is_updated,
            'hex': f"0x{product_state:08X}",
            'decimal': product_state
        }
    
    def test_wmi_connection(self, wmi_security_center):
        """Test: Verificar que podemos conectar a SecurityCenter2"""
        assert wmi_security_center is not None
        print("\n✅ Conexión a SecurityCenter2 exitosa")
    
    def test_antivirus_products_exist(self, wmi_security_center):
        """Test: Verificar que se detectan productos antivirus"""
        products = list(wmi_security_center.AntiVirusProduct())
        
        assert len(products) > 0, "No se detectaron productos antivirus"
        
        print(f"\n✅ Se detectaron {len(products)} producto(s) antivirus:")
        for av in products:
            print(f"   - {av.displayName}")
    
    def test_antivirus_details(self, wmi_security_center):
        """Test: Verificar detalles de cada antivirus"""
        products = list(wmi_security_center.AntiVirusProduct())
        
        print(f"\n{'='*80}")
        print("📋 DETALLES DE PRODUCTOS ANTIVIRUS")
        print("="*80)
        
        for i, av in enumerate(products, 1):
            state_info = self.decode_antivirus_state(av.productState)
            
            print(f"\n🛡️  PRODUCTO #{i}")
            print(f"{'─'*80}")
            print(f"Nombre:           {av.displayName}")
            print(f"Estado:           {state_info['status']}")
            print(f"Estado Raw:       {state_info['decimal']} ({state_info['hex']})")
            print(f"Habilitado:       {'✅ Sí' if state_info['enabled'] else '❌ No'}")
            print(f"Actualizado:      {'✅ Sí' if state_info['updated'] else '❌ No'}")
            print(f"GUID:             {av.instanceGuid}")
            
            # Assertions
            assert av.displayName, "El nombre del antivirus no puede estar vacío"
            assert av.productState > 0, "El productState debe ser mayor a 0"
            assert av.instanceGuid, "El GUID debe existir"
    
    def test_primary_antivirus_selection(self, wmi_security_center):
        """Test: Verificar selección correcta del antivirus principal"""
        products = list(wmi_security_center.AntiVirusProduct())
        
        windows_defender = None
        third_party = []
        
        for av in products:
            if 'Windows Defender' in av.displayName or 'Microsoft Defender' in av.displayName:
                windows_defender = av
            else:
                third_party.append(av)
        
        # Determinar principal
        if third_party:
            primary = third_party[0]
            print(f"\n✅ ANTIVIRUS PRINCIPAL: {primary.displayName} (Terceros)")
        elif windows_defender:
            primary = windows_defender
            print(f"\n✅ ANTIVIRUS PRINCIPAL: {primary.displayName} (Windows Defender)")
        else:
            primary = None
        
        assert primary is not None, "Debe haber al menos un antivirus principal"
        
        # Verificar que terceros tienen prioridad sobre Windows Defender
        if third_party and windows_defender:
            assert primary.displayName == third_party[0].displayName, \
                "El antivirus de terceros debe tener prioridad sobre Windows Defender"
            print("✅ Prioridad correcta: Terceros sobre Windows Defender")
    
    def test_firewall_products(self, wmi_security_center):
        """Test: Verificar productos firewall"""
        firewalls = list(wmi_security_center.FirewallProduct())
        
        print(f"\n{'='*80}")
        print("🔥 PRODUCTOS FIREWALL")
        print("="*80)
        
        if len(firewalls) == 0:
            print("\n⚠️  No se detectaron productos firewall (esto puede ser normal)")
        else:
            print(f"\n✅ Se detectaron {len(firewalls)} producto(s) firewall:")
            for fw in firewalls:
                state_info = self.decode_antivirus_state(fw.productState)
                print(f"\n🔥 {fw.displayName}")
                print(f"   Estado: {state_info['status']}")
                print(f"   Habilitado: {'✅ Sí' if state_info['enabled'] else '❌ No'}")
    
    def test_generate_payload(self, wmi_security_center):
        """Test: Generar payload como lo haría el agente"""
        products = list(wmi_security_center.AntiVirusProduct())
        
        windows_defender = None
        third_party_list = []
        primary = None
        
        for av in products:
            if 'Windows Defender' in av.displayName or 'Microsoft Defender' in av.displayName:
                windows_defender = av
            else:
                third_party_list.append(av.displayName)
                if primary is None:
                    primary = av
        
        if not primary and windows_defender:
            primary = windows_defender
        
        assert primary is not None, "Debe haber un antivirus principal para generar el payload"
        
        state_info = self.decode_antivirus_state(primary.productState)
        
        payload = {
            'antivirus_name': primary.displayName,
            'antivirus_version': None,  # Se obtendría de Win32_Product
            'protection_status': state_info['status_short'],
            'real_time_protection': state_info['real_time_protection'],
            'definitions_up_to_date': state_info['definitions_up_to_date'],
            'third_party_antivirus': third_party_list,
            'firewall_status': 'active',  # Se obtendría de FirewallProduct
        }
        
        print(f"\n{'='*80}")
        print("📤 PAYLOAD GENERADO (como lo enviaría el agente)")
        print("="*80)
        
        import json
        print(f"\n{json.dumps(payload, indent=2)}")
        
        # Assertions del payload
        assert payload['antivirus_name'], "antivirus_name no puede estar vacío"
        assert payload['protection_status'] in ['active', 'inactive'], \
            f"protection_status debe ser 'active' o 'inactive', no '{payload['protection_status']}'"
        assert isinstance(payload['real_time_protection'], bool), \
            "real_time_protection debe ser boolean"
        assert isinstance(payload['definitions_up_to_date'], bool), \
            "definitions_up_to_date debe ser boolean"
        assert isinstance(payload['third_party_antivirus'], list), \
            "third_party_antivirus debe ser una lista"
        
        print("\n✅ Payload válido y listo para enviar")


@pytest.mark.unit
class TestAntivirusStateDecoding:
    """Tests específicos para decodificación de estados"""
    
    def decode_state(self, state: int) -> dict:
        """Decodificar productState correctamente"""
        # Extraer nibbles
        product_enabled = (state & 0x000F0000) >> 16
        definitions_state = (state & 0x0000F000) >> 12
        
        # Producto habilitado si NO es 0x0
        is_enabled = product_enabled != 0x0
        
        # Definiciones actualizadas si ES 0x0
        is_updated = definitions_state == 0x0
        
        status_short = 'active' if is_enabled else 'inactive'
        
        return {
            'enabled': is_enabled,
            'updated': is_updated,
            'status_short': status_short
        }
    
    @pytest.mark.parametrize("state,expected", [
        # 0x061000: producto=0x6 (ON), definiciones=0x1 (OUT OF DATE)
        (397312, {'enabled': True, 'updated': False, 'status_short': 'active'}),
        
        # 0x041000: producto=0x4 (ON), definiciones=0x1 (OUT OF DATE)
        (266240, {'enabled': True, 'updated': False, 'status_short': 'active'}),
        
        # 0x060000: producto=0x6 (ON), definiciones=0x0 (UP TO DATE)
        (393216, {'enabled': True, 'updated': True, 'status_short': 'active'}),
        
        # 0x040000: producto=0x4 (ON), definiciones=0x0 (UP TO DATE)
        (262144, {'enabled': True, 'updated': True, 'status_short': 'active'}),
        
        # 0x000000: producto=0x0 (OFF), definiciones=0x0 (UP TO DATE)
        (0, {'enabled': False, 'updated': True, 'status_short': 'inactive'}),
        
        # 0x001000: producto=0x0 (OFF), definiciones=0x1 (OUT OF DATE)
        (4096, {'enabled': False, 'updated': False, 'status_short': 'inactive'}),
    ])
    def test_state_decoding(self, state, expected):
        """Test: Decodificar diferentes estados de antivirus"""
        result = self.decode_state(state)
        
        print(f"\n🔍 Estado: {state} (0x{state:06X})")
        print(f"   Producto bits: 0x{(state & 0x000F0000) >> 16:X} → {'ON' if result['enabled'] else 'OFF'}")
        print(f"   Definiciones bits: 0x{(state & 0x0000F000) >> 12:X} → {'UP TO DATE' if result['updated'] else 'OUT OF DATE'}")
        print(f"   Esperado: {expected}")
        print(f"   Obtenido: {result}")
        
        assert result['enabled'] == expected['enabled'], \
            f"enabled: esperado {expected['enabled']}, obtenido {result['enabled']}"
        assert result['updated'] == expected['updated'], \
            f"updated: esperado {expected['updated']}, obtenido {result['updated']}"
        assert result['status_short'] == expected['status_short'], \
            f"status: esperado {expected['status_short']}, obtenido {result['status_short']}"    f"status: esperado {expected['status_short']}, obtenido {result['status_short']}"