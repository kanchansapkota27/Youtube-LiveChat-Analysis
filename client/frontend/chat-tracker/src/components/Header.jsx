import React from 'react'

const Header = () => {
    return (
        <header className="bg-transparent text-gray-200 divide-y ml-18 border-b fixed inset-x-0">
            <div className="flex justify-between items-center h-14 mx-4">
                <div className="-ml-3">
                    <img src="https://www.cdnlogo.com/logos/y/57/youtube-icon.svg" className='w-20 h-8 aspect-auto' />
                </div>
                <div className="flex items-center justify-center flex-grow">
                    <input type="text" placeholder="Search" className=" text-gray-800 border rounded-l-xl border-gray-400 h-8  px-4 py-4 focus:outline-none focus:border-blue-600 w-3/5" />
                    <button className=" rounded-r-xl flex items-center justify-center h-8 w-16 border border-gray-400 focus:outline-none border-l-0">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                        </svg>
                    </button>
                </div>
                <div className="flex items-center justify-center space-x-4">
                    <button className="flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
  <path strokeLinecap="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
</svg>

                    </button>
                    <button className="flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
  <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
</svg>

                    </button>
                    <button>
                        <div className="h-8 w-8 rounded-full bg-blue-300 overflow-hidden object-cover">
                            <img className="object-cover" src="https://images.unsplash.com/photo-1570724061670-86a53c509dee?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=900&q=60" alt="" />
                        </div>
                    </button>
                </div>
            </div>
        </header>
    )
}

export default Header