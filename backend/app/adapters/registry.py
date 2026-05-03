from typing import Dict, Type, Optional
from app.adapters.base import BaseChannelAdapter
from app.adapters.whatsapp import WhatsAppAdapter
from app.adapters.mock import MockAdapter, TelegramAdapter, WebchatAdapter
import logging

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    Registry for channel adapters.
    
    Allows dynamic registration and retrieval of adapters for different channels.
    """

    def __init__(self):
        self._adapters: Dict[str, BaseChannelAdapter] = {}
        self._adapter_classes: Dict[str, Type[BaseChannelAdapter]] = {}
        self._initialize_default_adapters()

    def _initialize_default_adapters(self):
        """Initialize built-in adapters"""
        self.register_class("whatsapp", WhatsAppAdapter)
        self.register_class("mock", MockAdapter)
        self.register_class("telegram", TelegramAdapter)
        self.register_class("webchat", WebchatAdapter)

    def register_class(
        self,
        channel: str,
        adapter_class: Type[BaseChannelAdapter],
        **kwargs
    ):
        """Register an adapter class"""
        self._adapter_classes[channel] = adapter_class
        logger.info(f"Registered adapter class for channel: {channel}")

    def register_instance(self, channel: str, adapter: BaseChannelAdapter):
        """Register a concrete adapter instance"""
        self._adapters[channel] = adapter
        logger.info(f"Registered adapter instance for channel: {channel}")

    def get_adapter(self, channel: str, **kwargs) -> BaseChannelAdapter:
        """
        Get adapter for a channel.
        
        Returns existing instance if available, otherwise creates one.
        """
        # Return cached instance if exists
        if channel in self._adapters:
            return self._adapters[channel]

        # Create instance from registered class
        if channel in self._adapter_classes:
            adapter_class = self._adapter_classes[channel]
            adapter = adapter_class(**kwargs)
            self._adapters[channel] = adapter
            return adapter

        raise ValueError(f"No adapter registered for channel: {channel}")

    def get_all_adapters(self) -> Dict[str, BaseChannelAdapter]:
        """Get all registered adapters"""
        return self._adapters

    def list_channels(self) -> list:
        """List all available channels"""
        return list(set(list(self._adapters.keys()) + list(self._adapter_classes.keys())))


# Global registry instance
adapter_registry = AdapterRegistry()
