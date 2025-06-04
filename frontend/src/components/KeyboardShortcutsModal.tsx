import React from 'react';
import { XMarkIcon, CommandLineIcon, KeyboardIcon } from '@heroicons/react/24/outline';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const shortcuts = [
    {
      category: 'General',
      items: [
        { keys: ['Ctrl', 'Space'], description: 'Open Quick Actions panel' },
        { keys: ['Ctrl', 'F'], description: 'Search chat history' },
        { keys: ['Ctrl', 'N'], description: 'Start new chat' },
        { keys: ['Ctrl', ','], description: 'Open Settings' },
        { keys: ['Escape'], description: 'Close modals or clear focus' },
      ]
    },
    {
      category: 'File & Content',
      items: [
        { keys: ['Ctrl', 'U'], description: 'Upload files' },
        { keys: ['Ctrl', 'L'], description: 'Focus URL input' },        { keys: ['Ctrl', 'E'], description: 'Export chat' },
        { keys: ['Ctrl', 'D'], description: 'Open Document Manager' },
        { keys: ['Ctrl', 'P'], description: 'Toggle Performance Monitor' },
      ]
    },
    {
      category: 'Navigation',
      items: [
        { keys: ['↑', '↓'], description: 'Navigate between messages' },
        { keys: ['Enter'], description: 'Focus on input (from message)' },
        { keys: ['Shift', 'Enter'], description: 'New line in message input' },
      ]
    },
    {
      category: 'Chat Interaction',
      items: [
        { keys: ['Enter'], description: 'Send message' },
        { keys: ['Ctrl', 'Enter'], description: 'Send message (alternative)' },
        { keys: ['Tab'], description: 'Navigate between input fields' },
      ]
    }
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800/95 backdrop-blur-xl border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-teal-500 rounded-lg flex items-center justify-center">
              <KeyboardIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-200">Keyboard Shortcuts</h2>
              <p className="text-sm text-slate-400">Master AskRAG with these handy shortcuts</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg bg-slate-700/50 hover:bg-slate-600/50 transition-colors"
          >
            <XMarkIcon className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {shortcuts.map((category) => (
              <div key={category.category} className="space-y-4">
                <h3 className="text-lg font-medium text-slate-300 flex items-center gap-2">
                  <CommandLineIcon className="w-5 h-5 text-purple-400" />
                  {category.category}
                </h3>
                <div className="space-y-3">
                  {category.items.map((shortcut, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg border border-slate-600/30 hover:bg-slate-700/50 transition-colors"
                    >
                      <span className="text-slate-300 text-sm">{shortcut.description}</span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, keyIndex) => (
                          <React.Fragment key={keyIndex}>
                            {keyIndex > 0 && (
                              <span className="text-slate-500 text-xs mx-1">+</span>
                            )}
                            <kbd className="px-2 py-1 text-xs font-medium bg-slate-600 text-slate-200 rounded border border-slate-500 shadow-sm">
                              {key}
                            </kbd>
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Tips Section */}
          <div className="mt-8 p-4 bg-gradient-to-r from-purple-500/10 to-teal-500/10 border border-purple-500/20 rounded-lg">
            <h4 className="text-sm font-medium text-purple-300 mb-2">💡 Pro Tips</h4>
            <ul className="space-y-1 text-xs text-slate-400">
              <li>• Use arrow keys to quickly navigate through your conversation history</li>
              <li>• Hold Shift while pressing Enter to create multi-line messages</li>
              <li>• Press Escape to quickly close any open modal or clear message focus</li>
              <li>• Use Ctrl+F to search through your chat history when you have many messages</li>
              <li>• Press Tab to cycle through interactive elements in the interface</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-slate-700 bg-slate-800/50">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>Press</span>
            <kbd className="px-2 py-1 bg-slate-600 text-slate-300 rounded">?</kbd>
            <span>to open this help again</span>
          </div>
          <button
            onClick={onClose}
            className="btn-secondary px-4 py-2 text-sm"
          >
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
};

export default KeyboardShortcutsModal;
