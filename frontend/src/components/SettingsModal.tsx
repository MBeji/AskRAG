import React, { useState } from 'react';
import { 
  XMarkIcon,
  CogIcon,
  MoonIcon,
  SunIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  SparklesIcon,
  EyeIcon,
  ChatBubbleBottomCenterTextIcon,
  DocumentIcon
} from '@heroicons/react/24/outline';
import '../styles/modern-dark-theme.css';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface UserSettings {
  theme: 'dark' | 'light' | 'auto';
  soundEnabled: boolean;
  animationsEnabled: boolean;
  compactMode: boolean;
  autoScroll: boolean;
  showTimestamps: boolean;
  messagePreview: boolean;
  autoSave: boolean;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [settings, setSettings] = useState<UserSettings>({
    theme: 'dark',
    soundEnabled: true,
    animationsEnabled: true,
    compactMode: false,
    autoScroll: true,
    showTimestamps: true,
    messagePreview: true,
    autoSave: true
  });

  const [activeTab, setActiveTab] = useState<'appearance' | 'behavior' | 'advanced'>('appearance');

  const updateSetting = <K extends keyof UserSettings>(key: K, value: UserSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    // Save to localStorage
    localStorage.setItem('askrag-settings', JSON.stringify({ ...settings, [key]: value }));
  };

  const resetSettings = () => {
    const defaultSettings: UserSettings = {
      theme: 'dark',
      soundEnabled: true,
      animationsEnabled: true,
      compactMode: false,
      autoScroll: true,
      showTimestamps: true,
      messagePreview: true,
      autoSave: true
    };
    setSettings(defaultSettings);
    localStorage.setItem('askrag-settings', JSON.stringify(defaultSettings));
  };

  if (!isOpen) return null;

  const tabs = [
    { id: 'appearance', label: 'Appearance', icon: EyeIcon },
    { id: 'behavior', label: 'Behavior', icon: ChatBubbleBottomCenterTextIcon },
    { id: 'advanced', label: 'Advanced', icon: CogIcon }
  ];

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-teal-500 rounded-lg flex items-center justify-center">
              <CogIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-200">Settings</h2>
              <p className="text-sm text-slate-400">Customize your AskRAG experience</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors p-2 hover:bg-slate-800/50 rounded-lg"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-700">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-6 py-4 font-medium transition-all ${
                activeTab === tab.id
                  ? 'text-purple-400 border-b-2 border-purple-400 bg-slate-800/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/20'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto space-y-6">
          {/* Appearance Settings */}
          {activeTab === 'appearance' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <SparklesIcon className="w-5 h-5 text-purple-400" />
                  Theme & Visual
                </h3>

                {/* Theme Selection */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-3">Theme</label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: 'dark', label: 'Dark', icon: MoonIcon, desc: 'Dark mystical theme' },
                        { value: 'light', label: 'Light', icon: SunIcon, desc: 'Clean light theme' },
                        { value: 'auto', label: 'Auto', icon: CogIcon, desc: 'System preference' }
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => updateSetting('theme', option.value as any)}
                          className={`p-4 rounded-lg border-2 transition-all ${
                            settings.theme === option.value
                              ? 'border-purple-400 bg-purple-400/10 text-purple-300'
                              : 'border-slate-600 bg-slate-800/30 text-slate-400 hover:border-slate-500'
                          }`}
                        >
                          <option.icon className="w-6 h-6 mx-auto mb-2" />
                          <div className="text-sm font-medium">{option.label}</div>
                          <div className="text-xs opacity-70">{option.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Visual Options */}
                  <div className="grid grid-cols-2 gap-4">
                    <SettingToggle
                      label="Animations"
                      description="Enable smooth animations and transitions"
                      checked={settings.animationsEnabled}
                      onChange={(checked) => updateSetting('animationsEnabled', checked)}
                    />
                    <SettingToggle
                      label="Compact Mode"
                      description="Reduce spacing for more content"
                      checked={settings.compactMode}
                      onChange={(checked) => updateSetting('compactMode', checked)}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Behavior Settings */}
          {activeTab === 'behavior' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <ChatBubbleBottomCenterTextIcon className="w-5 h-5 text-teal-400" />
                  Chat Behavior
                </h3>

                <div className="grid grid-cols-2 gap-4">
                  <SettingToggle
                    label="Sound Effects"
                    description="Play sounds for notifications and messages"
                    checked={settings.soundEnabled}
                    onChange={(checked) => updateSetting('soundEnabled', checked)}
                    icon={settings.soundEnabled ? SpeakerWaveIcon : SpeakerXMarkIcon}
                  />
                  <SettingToggle
                    label="Auto Scroll"
                    description="Automatically scroll to new messages"
                    checked={settings.autoScroll}
                    onChange={(checked) => updateSetting('autoScroll', checked)}
                  />
                  <SettingToggle
                    label="Show Timestamps"
                    description="Display timestamps on messages"
                    checked={settings.showTimestamps}
                    onChange={(checked) => updateSetting('showTimestamps', checked)}
                  />
                  <SettingToggle
                    label="Message Preview"
                    description="Show preview of file contents"
                    checked={settings.messagePreview}
                    onChange={(checked) => updateSetting('messagePreview', checked)}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Advanced Settings */}
          {activeTab === 'advanced' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <DocumentIcon className="w-5 h-5 text-emerald-400" />
                  Data & Privacy
                </h3>

                <div className="space-y-4">
                  <SettingToggle
                    label="Auto Save"
                    description="Automatically save conversation history"
                    checked={settings.autoSave}
                    onChange={(checked) => updateSetting('autoSave', checked)}
                  />

                  <div className="pt-4 border-t border-slate-700">
                    <h4 className="text-md font-medium text-slate-300 mb-3">Data Management</h4>
                    <div className="grid grid-cols-2 gap-3">
                      <button className="btn-secondary text-sm py-2 px-4 bg-slate-800/50 border-slate-600 text-slate-300 hover:bg-slate-700/50">
                        Export Data
                      </button>
                      <button className="btn-secondary text-sm py-2 px-4 bg-slate-800/50 border-slate-600 text-slate-300 hover:bg-slate-700/50">
                        Clear History
                      </button>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-700">
                    <h4 className="text-md font-medium text-slate-300 mb-3">Reset Settings</h4>
                    <button 
                      onClick={resetSettings}
                      className="btn-secondary text-sm py-2 px-4 bg-red-900/20 border-red-600 text-red-400 hover:bg-red-900/30"
                    >
                      Reset to Defaults
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-slate-700 bg-slate-900/50">
          <div className="text-sm text-slate-400">
            Settings are automatically saved
          </div>
          <button
            onClick={onClose}
            className="btn-primary px-6 py-2 bg-gradient-to-r from-purple-500 to-teal-500 hover:from-purple-600 hover:to-teal-600"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

interface SettingToggleProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  icon?: React.ComponentType<any>;
}

const SettingToggle: React.FC<SettingToggleProps> = ({ 
  label, 
  description, 
  checked, 
  onChange, 
  icon: Icon 
}) => {
  return (
    <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          {Icon && <Icon className="w-5 h-5 text-slate-400 mt-0.5" />}
          <div>
            <div className="text-sm font-medium text-slate-200">{label}</div>
            <div className="text-xs text-slate-400 mt-1">{description}</div>
          </div>
        </div>
        <button
          onClick={() => onChange(!checked)}
          className={`relative w-11 h-6 rounded-full transition-colors ${
            checked ? 'bg-purple-500' : 'bg-slate-600'
          }`}
        >
          <div
            className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
              checked ? 'translate-x-5' : 'translate-x-0.5'
            }`}
          />
        </button>
      </div>
    </div>
  );
};

export default SettingsModal;
