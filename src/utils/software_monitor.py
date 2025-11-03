# src/utils/software_monitor.py

"""
Utilidad para monitorear software según configuración
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class SoftwareMonitor:
    """Monitorea software instalado según configuración"""
    
    def __init__(self, config_path: str = "config/monitored_software.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración de software a monitorear"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Configuración no encontrada: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error al leer configuración: {e}")
            return {}
    
    def get_critical_software(self, platform: str = None) -> List[Dict[str, Any]]:
        """Obtener lista de software crítico"""
        critical = []
        
        for category, data in self.config.items():
            if category.startswith('_') or category == 'monitoring_rules':
                continue
            
            if data.get('required', False):
                for software in data.get('software', []):
                    if platform:
                        if platform in software.get('platforms', []):
                            if software.get('alert_if_missing', False):
                                critical.append(software)
                    else:
                        if software.get('alert_if_missing', False):
                            critical.append(software)
        
        return critical
    
    def check_software_compliance(
        self, 
        installed_software: List[Dict[str, Any]], 
        platform: str
    ) -> Dict[str, Any]:
        """Verificar cumplimiento de software requerido"""
        
        installed_names = {sw.get('name', '').lower() for sw in installed_software}
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'compliant': True,
            'missing_critical': [],
            'outdated': [],
            'compliant_software': []
        }
        
        critical_software = self.get_critical_software(platform)
        
        for required in critical_software:
            required_name = required['name'].lower()
            
            if required_name not in installed_names:
                results['missing_critical'].append(required)
                results['compliant'] = False
            else:
                # Encontrar el software instalado
                installed = next(
                    (sw for sw in installed_software 
                     if sw.get('name', '').lower() == required_name),
                    None
                )
                
                if installed:
                    # Verificar versión mínima
                    min_version = required.get('min_version')
                    current_version = installed.get('version')
                    
                    if min_version and current_version:
                        if self._compare_versions(current_version, min_version) < 0:
                            results['outdated'].append({
                                'software': required,
                                'installed_version': current_version,
                                'min_version': min_version
                            })
                            results['compliant'] = False
                        else:
                            results['compliant_software'].append(required['name'])
                    else:
                        results['compliant_software'].append(required['name'])
        
        return results
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Comparar versiones (simplificado)"""
        try:
            v1_parts = [int(x) for x in version1.split('.')[:3]]
            v2_parts = [int(x) for x in version2.split('.')[:3]]
            
            # Rellenar con ceros
            while len(v1_parts) < 3:
                v1_parts.append(0)
            while len(v2_parts) < 3:
                v2_parts.append(0)
            
            if v1_parts < v2_parts:
                return -1
            elif v1_parts > v2_parts:
                return 1
            else:
                return 0
        except:
            return 0
    
    def get_all_monitored_software(self, platform: str = None) -> List[Dict[str, Any]]:
        """Obtener todo el software monitoreado"""
        monitored = []
        
        for category, data in self.config.items():
            if category.startswith('_') or category == 'monitoring_rules':
                continue
            
            for software in data.get('software', []):
                if platform:
                    if platform in software.get('platforms', []):
                        monitored.append({
                            'category': category,
                            **software
                        })
                else:
                    monitored.append({
                        'category': category,
                        **software
                    })
        
        return monitored
    
    def generate_compliance_report(
        self, 
        installed_software: List[Dict[str, Any]], 
        platform: str
    ) -> str:
        """Generar reporte de cumplimiento"""
        
        compliance = self.check_software_compliance(installed_software, platform)
        
        report = []
        report.append("=" * 60)
        report.append("SOFTWARE COMPLIANCE REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {compliance['timestamp']}")
        report.append(f"Platform: {compliance['platform']}")
        report.append(f"Status: {'✅ COMPLIANT' if compliance['compliant'] else '❌ NON-COMPLIANT'}")
        report.append("")
        
        if compliance['compliant_software']:
            report.append("✅ Compliant Software:")
            for sw in compliance['compliant_software']:
                report.append(f"   • {sw}")
            report.append("")
        
        if compliance['missing_critical']:
            report.append("❌ Missing Critical Software:")
            for sw in compliance['missing_critical']:
                report.append(f"   • {sw['name']} ({sw['vendor']})")
            report.append("")
        
        if compliance['outdated']:
            report.append("⚠️  Outdated Software:")
            for item in compliance['outdated']:
                report.append(f"   • {item['software']['name']}")
                report.append(f"     Installed: {item['installed_version']}")
                report.append(f"     Required:  {item['min_version']}")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


# Ejemplo de uso
if __name__ == "__main__":
    monitor = SoftwareMonitor()
    
    # Software instalado de ejemplo
    installed = [
        {'name': 'Microsoft Office', 'version': '16.50'},
        {'name': 'Google Chrome', 'version': '121.0'},
        {'name': 'Python', 'version': '3.11.0'}
    ]
    
    # Verificar cumplimiento
    report = monitor.generate_compliance_report(installed, 'Darwin')
    print(report)
