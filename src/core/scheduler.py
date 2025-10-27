# src/core/scheduler.py

"""
Módulo de programación de tareas
Maneja la ejecución periódica de trabajos y tareas programadas
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, List
from enum import Enum


class JobStatus(Enum):
    """Estados posibles de un trabajo"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """
    Representa un trabajo programado
    """
    
    def __init__(
        self,
        name: str,
        func: Callable,
        interval: int = None,
        run_at: datetime = None,
        args: tuple = None,
        kwargs: dict = None
    ):
        """
        Inicializa un trabajo
        
        Args:
            name: Nombre descriptivo del trabajo
            func: Función a ejecutar
            interval: Intervalo en segundos (para trabajos recurrentes)
            run_at: Fecha/hora específica de ejecución (para trabajos únicos)
            args: Argumentos posicionales para la función
            kwargs: Argumentos con nombre para la función
        """
        self.name = name
        self.func = func
        self.interval = interval
        self.run_at = run_at
        self.args = args or ()
        self.kwargs = kwargs or {}
        
        self.status = JobStatus.PENDING
        self.last_run = None
        self.next_run = run_at if run_at else datetime.now()
        self.run_count = 0
        self.error_count = 0
        self.last_error = None
        
        self.thread = None
        self.is_running = False
        self.cancelled = False
    
    def should_run(self) -> bool:
        """
        Verifica si el trabajo debe ejecutarse
        
        Returns:
            bool: True si debe ejecutarse
        """
        if self.cancelled:
            return False
        
        if self.is_running:
            return False
        
        return datetime.now() >= self.next_run
    
    def run(self):
        """Ejecuta el trabajo"""
        if self.cancelled or self.is_running:
            return
        
        self.is_running = True
        self.status = JobStatus.RUNNING
        
        try:
            # Ejecutar la función
            result = self.func(*self.args, **self.kwargs)
            
            # Actualizar estadísticas
            self.last_run = datetime.now()
            self.run_count += 1
            self.status = JobStatus.COMPLETED
            
            # Calcular próxima ejecución si es recurrente
            if self.interval:
                self.next_run = datetime.now() + timedelta(seconds=self.interval)
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.status = JobStatus.FAILED
            raise
            
        finally:
            self.is_running = False
    
    def cancel(self):
        """Cancela el trabajo"""
        self.cancelled = True
        self.status = JobStatus.CANCELLED
    
    def __str__(self) -> str:
        return (
            f"Job({self.name}, status={self.status.value}, "
            f"next_run={self.next_run}, run_count={self.run_count})"
        )
    
    def __repr__(self) -> str:
        return self.__str__()


class Scheduler:
    """
    Programador de tareas que ejecuta trabajos en segundo plano
    """
    
    def __init__(self):
        """Inicializa el scheduler"""
        self.logger = logging.getLogger('ITAgent.Scheduler')
        self.jobs: Dict[str, Job] = {}
        self.running = False
        self.thread = None
        
        self.logger.info("Scheduler inicializado")
    
    def add_job(
        self,
        name: str,
        func: Callable,
        interval: int = None,
        run_at: datetime = None,
        args: tuple = None,
        kwargs: dict = None
    ) -> Job:
        """
        Agrega un trabajo al scheduler
        
        Args:
            name: Nombre único del trabajo
            func: Función a ejecutar
            interval: Intervalo en segundos (para trabajos recurrentes)
            run_at: Fecha/hora específica (para trabajos únicos)
            args: Argumentos posicionales
            kwargs: Argumentos con nombre
            
        Returns:
            Job: El trabajo creado
        """
        if name in self.jobs:
            self.logger.warning(f"Trabajo '{name}' ya existe. Será reemplazado.")
        
        job = Job(name, func, interval, run_at, args, kwargs)
        self.jobs[name] = job
        
        self.logger.info(
            f"✓ Trabajo agregado: {name} "
            f"(intervalo: {interval}s)" if interval else "(ejecución única)"
        )
        
        return job
    
    def add_interval_job(
        self,
        name: str,
        func: Callable,
        interval: int,
        args: tuple = None,
        kwargs: dict = None
    ) -> Job:
        """
        Agrega un trabajo que se ejecuta periódicamente
        
        Args:
            name: Nombre del trabajo
            func: Función a ejecutar
            interval: Intervalo en segundos
            args: Argumentos posicionales
            kwargs: Argumentos con nombre
            
        Returns:
            Job: El trabajo creado
        """
        return self.add_job(name, func, interval=interval, args=args, kwargs=kwargs)
    
    def add_cron_job(
        self,
        name: str,
        func: Callable,
        hour: int = 0,
        minute: int = 0,
        args: tuple = None,
        kwargs: dict = None
    ) -> Job:
        """
        Agrega un trabajo que se ejecuta diariamente a una hora específica
        
        Args:
            name: Nombre del trabajo
            func: Función a ejecutar
            hour: Hora del día (0-23)
            minute: Minuto (0-59)
            args: Argumentos posicionales
            kwargs: Argumentos con nombre
            
        Returns:
            Job: El trabajo creado
        """
        # Calcular próxima ejecución
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Si ya pasó hoy, programar para mañana
        if next_run <= now:
            next_run += timedelta(days=1)
        
        # Intervalo de 24 horas
        job = self.add_job(
            name, 
            func, 
            interval=86400,  # 24 horas en segundos
            run_at=next_run,
            args=args,
            kwargs=kwargs
        )
        
        self.logger.info(f"✓ Trabajo cron agregado: {name} (ejecuta a las {hour:02d}:{minute:02d})")
        
        return job
    
    def remove_job(self, name: str) -> bool:
        """
        Elimina un trabajo del scheduler
        
        Args:
            name: Nombre del trabajo
            
        Returns:
            bool: True si se eliminó correctamente
        """
        if name in self.jobs:
            job = self.jobs[name]
            job.cancel()
            del self.jobs[name]
            self.logger.info(f"✓ Trabajo eliminado: {name}")
            return True
        else:
            self.logger.warning(f"⚠️  Trabajo no encontrado: {name}")
            return False
    
    def get_job(self, name: str) -> Optional[Job]:
        """
        Obtiene un trabajo por nombre
        
        Args:
            name: Nombre del trabajo
            
        Returns:
            Job: El trabajo o None si no existe
        """
        return self.jobs.get(name)
    
    def get_all_jobs(self) -> List[Job]:
        """
        Obtiene todos los trabajos
        
        Returns:
            list: Lista de trabajos
        """
        return list(self.jobs.values())
    
    def start(self):
        """Inicia el scheduler en un hilo separado"""
        if self.running:
            self.logger.warning("Scheduler ya está ejecutándose")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        self.logger.info("🚀 Scheduler iniciado")
    
    def stop(self):
        """Detiene el scheduler"""
        if not self.running:
            self.logger.warning("Scheduler no está ejecutándose")
            return
        
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        self.logger.info("⏹️  Scheduler detenido")
    
    def _run_loop(self):
        """Loop principal del scheduler"""
        self.logger.debug("Loop del scheduler iniciado")
        
        while self.running:
            try:
                # Verificar cada trabajo
                for job_name, job in list(self.jobs.items()):
                    if not self.running:
                        break
                    
                    # Verificar si el trabajo debe ejecutarse
                    if job.should_run():
                        self._execute_job(job)
                
                # Pequeña pausa para no consumir CPU
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error en el loop del scheduler: {e}", exc_info=True)
                time.sleep(5)
        
        self.logger.debug("Loop del scheduler terminado")
    
    def _execute_job(self, job: Job):
        """
        Ejecuta un trabajo en un hilo separado
        
        Args:
            job: Trabajo a ejecutar
        """
        def run_job():
            try:
                self.logger.info(f"▶️  Ejecutando trabajo: {job.name}")
                start_time = time.time()
                
                job.run()
                
                elapsed = time.time() - start_time
                self.logger.info(
                    f"✓ Trabajo completado: {job.name} "
                    f"(tiempo: {elapsed:.2f}s, ejecuciones: {job.run_count})"
                )
                
            except Exception as e:
                self.logger.error(
                    f"✗ Error en trabajo {job.name}: {e}",
                    exc_info=True
                )
        
        # Ejecutar en un hilo separado
        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()
    
    def pause_job(self, name: str) -> bool:
        """
        Pausa un trabajo (no se ejecutará hasta que se reanude)
        
        Args:
            name: Nombre del trabajo
            
        Returns:
            bool: True si se pausó correctamente
        """
        job = self.get_job(name)
        if job:
            job.next_run = datetime.max  # Poner en el futuro lejano
            self.logger.info(f"⏸️  Trabajo pausado: {name}")
            return True
        return False
    
    def resume_job(self, name: str) -> bool:
        """
        Reanuda un trabajo pausado
        
        Args:
            name: Nombre del trabajo
            
        Returns:
            bool: True si se reanudó correctamente
        """
        job = self.get_job(name)
        if job and job.interval:
            job.next_run = datetime.now()
            self.logger.info(f"▶️  Trabajo reanudado: {name}")
            return True
        return False
    
    def run_job_now(self, name: str) -> bool:
        """
        Ejecuta un trabajo inmediatamente (sin esperar el intervalo)
        
        Args:
            name: Nombre del trabajo
            
        Returns:
            bool: True si se ejecutó correctamente
        """
        job = self.get_job(name)
        if job:
            self.logger.info(f"▶️  Ejecutando trabajo manualmente: {name}")
            self._execute_job(job)
            return True
        return False
    
    def get_status(self) -> Dict:
        """
        Obtiene el estado del scheduler
        
        Returns:
            dict: Estado del scheduler
        """
        return {
            'running': self.running,
            'total_jobs': len(self.jobs),
            'active_jobs': sum(1 for j in self.jobs.values() if not j.cancelled),
            'jobs': [
                {
                    'name': job.name,
                    'status': job.status.value,
                    'last_run': job.last_run.isoformat() if job.last_run else None,
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'run_count': job.run_count,
                    'error_count': job.error_count,
                    'interval': job.interval
                }
                for job in self.jobs.values()
            ]
        }
    
    def clear_all_jobs(self):
        """Elimina todos los trabajos"""
        for job_name in list(self.jobs.keys()):
            self.remove_job(job_name)
        
        self.logger.info("🗑️  Todos los trabajos eliminados")
    
    def __enter__(self):
        """Context manager - inicio"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - fin"""
        self.stop()
    
    def __str__(self) -> str:
        return (
            f"Scheduler(running={self.running}, "
            f"jobs={len(self.jobs)})"
        )
    
    def __repr__(self) -> str:
        return self.__str__()


# Instancia global del scheduler (opcional)
_global_scheduler = None


def get_scheduler() -> Scheduler:
    """
    Obtiene la instancia global del scheduler
    
    Returns:
        Scheduler: Instancia del scheduler
    """
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = Scheduler()
    return _global_scheduler