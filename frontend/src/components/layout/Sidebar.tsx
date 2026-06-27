import { NavLink } from 'react-router-dom'

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'People', href: '/people', icon: '👥' },
  { name: 'Templates', href: '/templates', icon: '📝' },
  { name: 'Settings', href: '/settings', icon: '⚙️' },
]

export function Sidebar() {
  return (
    <div className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 lg:block hidden">
      <div className="flex items-center h-16 px-6 border-b border-gray-200">
        <span className="text-xl font-bold text-primary-600">NetworkPilot</span>
      </div>
      <nav className="mt-6 px-3">
        <div className="space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              end={item.href === '/'}
              className={({ isActive }) =>
                `flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <span className="mr-3 text-lg">{item.icon}</span>
              {item.name}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
