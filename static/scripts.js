let tweets = [];
let currentIndex = 0;

// Character counter for tweet composer
document
.getElementById("tweetText")
.addEventListener("input", function () {
    const count = this.value.length;
    document.getElementById("charCount").textContent = count;
    if (count > 280) {
    this.value = this.value.substring(0, 280);
    }
});

// Post tweet immediately
function postTweet() {
const text = document.getElementById("tweetText").value;
if (!text) return;

fetch("/post_tweet", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tweet: text }),
})
    .then((response) => response.json())
    .then((data) => {
    if (data.status === "success") {
        document.getElementById("tweetText").value = "";
        document.getElementById("charCount").textContent = "0";
        alert("Tweet posted successfully!");
    }
    })
    .catch((error) => alert("Error posting tweet"));
}

// Modal controls
function openReviewModal() {
document.getElementById("reviewModal").style.display = "block";
loadTweets();
}

function closeReviewModal() {
document.getElementById("reviewModal").style.display = "none";
}

// Load and display tweets
function loadTweets() {
Promise.all([
    fetch("/tweets").then((r) => r.json()),
    fetch("/schedule").then((r) => r.json()),
])
    .then(([pendingTweets, scheduledTweets]) => {
    tweets = pendingTweets;
    updateScheduleTable(scheduledTweets);
    updateTweetCounter();
    showCurrentTweet();
    })
    .catch((error) => {
    console.error("Error:", error);
    document.getElementById("modal-tweet-container").innerHTML =
        "Error loading tweets. Please try again.";
    });
}

function updateTweetCounter() {
document.getElementById("currentTweetNum").textContent =
    tweets.length > 0 ? currentIndex + 1 : 0;
document.getElementById("totalTweets").textContent = tweets.length;
}

function showCurrentTweet() {
const container = document.getElementById("modal-tweet-container");
if (!tweets || tweets.length === 0) {
    container.innerHTML = `
            <div class="text-center">
                <p class="text-muted">No tweets to review!</p>
                <button onclick="closeReviewModal()" class="btn btn-secondary">Close</button>
            </div>`;
    return;
}
const tweet = tweets[currentIndex];
container.innerHTML = `
        <div class="tweet-content">
            <p class="fs-5">${tweet.tweet}</p>
        </div>
    `;
updateTweetCounter();
}

function approveTweet() {
    const tweet = tweets[currentIndex];
    fetch("/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: tweet.id }),
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.status === "success") {
            // Show scheduling confirmation with full date/time
            alert(`Tweet approved and scheduled for ${data.display_time}`);
            nextTweet();
            loadSchedule();
        } else {
            alert("Error approving tweet: " + data.message);
        }
    })
    .catch((error) => alert("Error approving tweet"));
}

function rejectTweet() {
const tweet = tweets[currentIndex];
fetch("/reject", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: tweet.id }),
})
    .then(() => nextTweet())
    .catch((error) => alert("Error rejecting tweet"));
}

function nextTweet() {
tweets.splice(currentIndex, 1);
if (tweets.length === 0) {
    showCurrentTweet();
    return;
}
if (currentIndex >= tweets.length) {
    currentIndex = 0;
}
showCurrentTweet();
loadSchedule();
}

function loadSchedule() {
fetch("/schedule")
    .then((r) => r.json())
    .then((data) => {
    console.log("Schedule data:", data); // Debug log
    updateScheduleTable(data);
    })
    .catch((error) => {
    console.error("Error loading schedule:", error);
    });
}

function updateScheduleTable(scheduleData) {
    const tbody = document.getElementById("schedule-body");
    if (!tbody || !Array.isArray(scheduleData)) return;

    tbody.innerHTML = scheduleData.map(tweet => {
        const scheduledDate = tweet.scheduled_time ? 
            new Date(tweet.scheduled_time) : null;
        
        const formattedTime = scheduledDate ? 
            scheduledDate.toLocaleString('en-US', {
                timeZone: 'Asia/Kolkata',
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            }) + ' IST' : 
            'Not scheduled';
            
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4">${tweet.tweet}</td>
                <td class="px-6 py-4">
                    <span class="status-badge status-${tweet.status.toLowerCase()}">${tweet.status}</span>
                </td>
                <td class="px-6 py-4 text-gray-600">
                    ${formattedTime}
                </td>
                <td class="px-6 py-4">
                    <div class="flex space-x-2">
                        <button onclick="deleteTweet(${tweet.id})" 
                            class="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                            <i class="fas fa-trash"></i>
                        </button>
                        <button onclick="postNowTweet(${tweet.id})" 
                            class="p-2 text-green-600 hover:bg-green-50 rounded-lg">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Add this helper function to format the schedule time
function formatScheduleTime(dateString) {
    if (!dateString) return "Pending";
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        timeZone: 'Asia/Kolkata',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

// Add all initialization code inside DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
    const scheduleContainer = document.getElementById("schedule-container");
    scheduleContainer.style.maxHeight = "400px";
    scheduleContainer.style.overflowY = "auto";

    // Automatically load the schedule on page load
    loadSchedule();

    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');

    function toggleSidebar() {
        sidebar.classList.toggle('-translate-x-full');
        // Adjust main content margin when sidebar is toggled
        if (window.innerWidth < 1024) {  // Only on mobile
            mainContent.classList.toggle('ml-64');
        }
    }

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleSidebar();
        });

        // Close sidebar when clicking outside
        document.addEventListener('click', function(e) {
            if (window.innerWidth < 1024) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.add('-translate-x-full');
                    mainContent.classList.remove('ml-64');
                }
            }
        });

        // Handle window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth >= 1024) {
                mainContent.classList.add('lg:ml-64');
                sidebar.classList.remove('-translate-x-full');
            } else {
                mainContent.classList.remove('lg:ml-64');
                sidebar.classList.add('-translate-x-full');
            }
        });
    }

    // Sidebar collapse functionality
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
    const sidebarCollapseIcon = document.getElementById('sidebarCollapseIcon');
    let isCollapsed = false;

    if (sidebarCollapseBtn) {
        sidebarCollapseBtn.addEventListener('click', function() {
            isCollapsed = !isCollapsed;
            
            // Toggle sidebar width
            sidebar.style.width = isCollapsed ? '64px' : '256px';
            
            // Toggle main content margin
            mainContent.style.marginLeft = isCollapsed ? '64px' : '256px';
            
            // Rotate icon
            sidebarCollapseIcon.style.transform = isCollapsed ? 'rotate(180deg)' : '';
            
            // Hide/show text
            const textElements = sidebar.querySelectorAll('span:not(.text-xl)');
            textElements.forEach(el => {
                el.style.display = isCollapsed ? 'none' : 'inline';
            });
            
            // Adjust logo section
            const logo = sidebar.querySelector('.text-xl');
            logo.style.display = isCollapsed ? 'none' : 'block';
            
            // Center icons when collapsed
            const iconContainers = sidebar.querySelectorAll('a');
            iconContainers.forEach(container => {
                container.classList.toggle('justify-center', isCollapsed);
            });
        });
    }
});

// Upload Modal controls
function openUploadModal() {
document.getElementById("uploadModal").style.display = "block";
}

function closeUploadModal() {
document.getElementById("uploadModal").style.display = "none";
}

// Handle tweet uploads
document
.getElementById("uploadForm")
.addEventListener("submit", function (e) {
    e.preventDefault();
    const tweetsText = document.getElementById("tweetsInput").value;
    const tweets = tweetsText
    .split("\n")
    .map((tweet) => tweet.trim())
    .filter((tweet) => tweet.length > 0);
    if (tweets.length === 0) {
    alert("Please enter at least one tweet.");
    return;
    }

    fetch("/upload_tweets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tweets: tweets }),
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.status === "success") {
        alert("Tweets uploaded successfully!");
        closeUploadModal();
        loadSchedule(); // Refresh the tweet list
        } else {
        alert("Error uploading tweets: " + data.message);
        }
    })
    .catch((error) => alert("Error uploading tweets."));
});

// Delete tweet function
function deleteTweet(tweetId) {
if (!confirm("Are you sure you want to delete this tweet?")) return;
fetch("/delete_tweet", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: tweetId }),
})
    .then((response) => response.json())
    .then((data) => {
    if (data.status === "success") {
        alert("Tweet deleted successfully!");
        loadSchedule();
    } else {
        alert("Error deleting tweet: " + data.message);
    }
    })
    .catch((error) => alert("Error deleting tweet."));
}

// Delete current tweet function
function deleteCurrentTweet() {
const tweet = tweets[currentIndex];
if (!confirm("Are you sure you want to delete this tweet?")) return;
fetch("/delete_tweet", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: tweet.id }),
})
    .then((response) => response.json())
    .then((data) => {
    if (data.status === "success") {
        alert("Tweet deleted successfully!");
        nextTweet();
    } else {
        alert("Error deleting tweet: " + data.message);
    }
    })
    .catch((error) => alert("Error deleting tweet."));
}

// Post tweet immediately from schedule
function postNowTweet(tweetId) {
if (!confirm("Are you sure you want to post this tweet immediately?"))
    return;
fetch("/post_now_tweet", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: tweetId }),
})
    .then((response) => response.json())
    .then((data) => {
    if (data.status === "success") {
        alert("Tweet posted successfully!");
        loadSchedule();
    } else {
        alert("Error posting tweet: " + data.message);
    }
    })
    .catch((error) => alert("Error posting tweet."));
}

// Add timezone conversion helper function
function getISTDateTime(date) {
    return new Date(date).toLocaleString('en-US', { 
        timeZone: 'Asia/Kolkata',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

// Update formatDateTime function
function formatDateTime(dateString) {
    if (!dateString) return "Pending";
    return getISTDateTime(dateString);
}

// Open Update Time Modal with validation
function openUpdateTimeModal(tweetId) {
    const modal = document.getElementById("updateTimeModal");
    const dateInput = document.getElementById("newScheduledTime");
    
    // Set minimum datetime to 5 minutes from now in IST
    const now = new Date();
    const istOffset = 330; // IST offset in minutes (UTC+5:30)
    const minDate = new Date(now.getTime() + 5 * 60 * 1000);
    const defaultDate = new Date(now.getTime() + 30 * 60 * 1000);
    
    // Convert to ISO string and adjust for local input
    dateInput.min = minDate.toISOString().slice(0, 16);
    dateInput.value = defaultDate.toISOString().slice(0, 16);
    
    document.getElementById("updateTweetId").value = tweetId;
    modal.style.display = "block";
}

// Close Update Time Modal
function closeUpdateTimeModal() {
document.getElementById("updateTimeModal").style.display = "none";
}

// Handle Update Time Form Submission with better validation
document.getElementById("updateTimeForm").addEventListener("submit", function (e) {
    e.preventDefault();
    const tweetId = document.getElementById("updateTweetId").value;
    const newTime = document.getElementById("newScheduledTime").value;
    const scheduledDate = new Date(newTime);
    const now = new Date();

    if (!newTime) {
        alert("Please select a scheduling time.");
        return;
    }

    if (scheduledDate <= now) {
        alert("Please select a future time for scheduling.");
        return;
    }

    if (scheduledDate < new Date(now.getTime() + 5 * 60 * 1000)) {
        alert("Please schedule at least 5 minutes in advance.");
        return;
    }

    fetch("/update_schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            id: tweetId, 
            scheduled_time: newTime,
            timezone: 'Asia/Kolkata' // Explicitly set IST timezone
        }),
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.status === "success") {
            closeUpdateTimeModal();
            loadSchedule();
            const scheduledTimeIST = getISTDateTime(scheduledDate);
            alert(`Tweet scheduled successfully for ${scheduledTimeIST}!`);
        } else {
            alert("Error scheduling tweet: " + data.message);
        }
    })
    .catch((error) => alert("Error updating scheduled time."));
});

// Format datetime for display
function formatDateTime(dateString) {
    if (!dateString) return "Pending";
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('default', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    }).format(date);
}

// Handle Update Time Form Submission
document
.getElementById("updateTimeForm")
.addEventListener("submit", function (e) {
    e.preventDefault();
    const tweetId = document.getElementById("updateTweetId").value;
    const newTime = document.getElementById("newScheduledTime").value;

    if (!newTime) {
    alert("Please select a new scheduled time.");
    return;
    }

    fetch("/update_schedule", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: tweetId, scheduled_time: newTime }),
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.status === "success") {
        alert("Scheduled time updated successfully!");
        closeUpdateTimeModal();
        loadSchedule();
        } else {
        alert("Error updating time: " + data.message);
        }
    })
    .catch((error) => alert("Error updating scheduled time."));
});

// Update schedule refresh interval to match backend timing (12-20 minutes)
function initScheduleRefresh() {
    // Initial load
    refreshSchedule();
    
    // Random interval between 12-20 minutes (720000-1200000 milliseconds)
    const minInterval = 720000;
    const maxInterval = 1200000;
    
    function scheduleNextRefresh() {
        const randomInterval = Math.floor(Math.random() * (maxInterval - minInterval + 1)) + minInterval;
        console.log(`Next schedule refresh in ${Math.round(randomInterval/1000/60)} minutes`);
        
        setTimeout(() => {
            refreshSchedule();
            scheduleNextRefresh();
        }, randomInterval);
    }
    
    scheduleNextRefresh();
}

function refreshSchedule() {
    fetch("/schedule")
        .then((response) => response.json())
        .then((data) => {
            updateScheduleTable(data);
        })
        .catch((error) => console.error("Error fetching schedule:", error));
}

// Update the schedule table with current data
function updateScheduleTable(scheduleData) {
    const tbody = document.getElementById("schedule-body");
    if (!tbody) return;

    tbody.innerHTML = "";
    scheduleData.forEach((tweet) => {
        const row = document.createElement("tr");
        
        // Format the scheduled time to be more readable
        const scheduledTime = tweet.scheduled_time ? 
            new Date(tweet.scheduled_time).toLocaleString() : 
            'Not scheduled';
            
        row.innerHTML = `
            <td class="px-6 py-4 text-sm text-gray-800">${tweet.tweet}</td>
            <td class="px-6 py-4">
                <span class="status-badge status-${tweet.status.toLowerCase()}">${tweet.status}</span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">${scheduledTime}</td>
            <td class="px-6 py-4">
                <div class="flex space-x-2">
                    <button class="p-2 text-red-600 hover:bg-red-50 rounded-lg" onclick="deletePost(${tweet.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg" onclick="postNow(${tweet.id})">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </td>
            <td class="px-6 py-4">
                <button class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg" onclick="openUpdateTimeModal(${tweet.id})">
                    <i class="fas fa-clock"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Call initScheduleRefresh when the page loads
document.addEventListener('DOMContentLoaded', initScheduleRefresh);

// Add or update this function in your scripts.js file

function submitUpdateTimeForm(event) {
    event.preventDefault();
    const tweetId = document.getElementById('updateTweetId').value;
    const scheduledTime = document.getElementById('newScheduledTime').value;
    
    // Format the date to match backend expectation
    const formattedDate = scheduledTime.replace('T', ' ');
    
    fetch('/update_schedule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id: tweetId,
            scheduled_time: formattedDate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            closeUpdateTimeModal();
            // Refresh the schedule display
            fetchSchedule();
        } else {
            alert('Error updating schedule: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating schedule');
    });
}

// Make sure this line is present in your initialization code
document.getElementById('updateTimeForm').addEventListener('submit', submitUpdateTimeForm);