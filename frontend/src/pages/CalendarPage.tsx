import { Calendar as CalendarIcon, Plus } from 'lucide-react';
import { useState } from 'react';
import { format, addMonths, subMonths, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, startOfWeek, endOfWeek } from 'date-fns';
import { de } from 'date-fns/locale';

export const CalendarPage = () => {
  const [currentMonth, setCurrentMonth] = useState(new Date());

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const startDate = startOfWeek(monthStart, { locale: de });
  const endDate = endOfWeek(monthEnd, { locale: de });
  const days = eachDayOfInterval({ start: startDate, end: endDate });

  const weekDays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center">
          <CalendarIcon className="w-6 h-6 mr-2 text-primary-600" />
          <h1 className="page-title">Kalender</h1>
        </div>
        
        <button className="btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          Neuer Termin
        </button>
      </div>

      <div className="card">
        <div className="flex items-center justify-between p-4 border-b">
          <button
            onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            ←
          </button>
          
          <h2 className="text-lg font-semibold">
            {format(currentMonth, 'MMMM yyyy', { locale: de })}
          </h2>
          
          <button
            onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            →
          </button>
        </div>

        <div className="p-4">
          <div className="grid grid-cols-7 gap-1">
            {weekDays.map((day) => (
              <div key={day} className="p-2 text-center text-sm font-medium text-gray-500">
                {day}
              </div>
            ))}
            
            {days.map((day, idx) => (
              <div
                key={idx}
                className={`p-2 min-h-[100px] border rounded-lg ${
                  !isSameMonth(day, currentMonth) ? 'bg-gray-50 text-gray-400' : 'bg-white'
                } ${isSameDay(day, new Date()) ? 'ring-2 ring-primary-500' : ''}`}
              >
                <span className="text-sm">{format(day, 'd')}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
